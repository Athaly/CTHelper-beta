import logging
import sqlite3
from database import *

from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext

# Bot token configuration
TOKEN = '6497209609:AAEEeCN2PR5s38p21R1SQgTlKi9N1vvvBp0'  # Replace with your token
bot = Bot(token=TOKEN)

# Updater definition in the global scope
updater = Updater(bot=bot)

# Logger configuration to view debug messages
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Store the channel to which links should be forwarded
channel_id = None
# Set of participating users
participating_users = set()

# Function to handle messages
def handle_message(update, context):
    if update.message is not None and update.message.text is not None:
        chat_id = update.effective_chat.id
        message_text = update.message.text
        user = update.message.from_user
        name = user.first_name

        if channel_id and "Duración de la partida" in message_text and user_participating(name):
            # Remove the -100 prefix from the chat ID if it is present
            if str(chat_id).startswith('-100'):
                chat_id = str(chat_id)[3:]
            message_link = f"https://t.me/c/{chat_id}/{update.message.message_id}"
            bot.send_message(chat_id=channel_id, text=message_link)

            # Process the match result (assuming the message contains the result)
            if "Ganó" in message_text:
                increment_wins(get_user_id(name))
            elif "Perdió" in message_text:
                increment_losses(get_user_id(name))

            # Increment the matches played counter
            increment_matches_played(get_user_id(name))

# Function to check if a user is participating
def user_participating(name):
    return name in participating_users

# Function to set the target channel
def set_channel(update, context):
    global channel_id
    chat_id = update.message.chat_id
    # Get the last element of the string
    channel_name = update.message.text.split()[-1]
    if channel_name.startswith('@'):
        channel_id = channel_name  # Update the target channel
        bot.send_message(
            chat_id=chat_id, text=f"Canal actualizado a: {channel_name}")
    else:
        bot.send_message(
            chat_id=chat_id, text=f"Nombre de canal invalido: {channel_name}")

#  Join the tournament
def join_tournament(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name
    user_id = user.id  # Get the user ID

    # Create a connection to the database and a cursor
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()

    # Check if the user is already in the tournament
    if get_user_id(name):
        update.message.reply_text(f'Ya estás en el torneo, {name}.')
    else:
        # Call the function to insert the player into the database
        if insert_player(user_id, name):
            participating_users.add(name)
            update.message.reply_text(f'Has entrado en el torneo, {name}!')
        else:
            update.message.reply_text(
                f'Ya estás en el torneo, {name}.')

    # Close the database connection after use
    conn.close()

# Lleave the tournament
def leave_tournament(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name

    # Create a connection to the database and a cursor
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()

    # Get the user_id of the player
    user_id = get_user_id(name)

    if user_id is not None:
        if name in participating_users:
            participating_users.remove(name)

            # Delete the player from the database
            delete_player(user_id)  # Pass only the user_id as an argument
            conn.commit()

            update.message.reply_text(f'Has abandonado el torneo, {name}.')
        else:
            update.message.reply_text(f'No estabas en el torneo, {name}.')
    else:
        update.message.reply_text(f'No estabas en el torneo, {name}.')

    # Close the database connection after use
    conn.close()

# Function to show the leaderboard
def show_leaderboard(update, context):
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()
    limit = 5  # Show the top 5 by default
    if len(context.args) > 0:
        try:
            limit = int(context.args[0])
        except ValueError:
            update.message.reply_text("Por favor ingresa un numero valido.")
            return

    leaderboard = get_leaderboard(cursor, limit)  # Pass the cursor as an argument
    if leaderboard:
        message = "Leaderboard:\n\n"
        for i, (username, wins, losses, win_percentage) in enumerate(leaderboard, start=1):
            message += f"{i}. {username}: Victorias: {wins}, Derrotas: {losses}, Porcentaje de victoria: {win_percentage:.2f}%\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text("Aun no hay jugadores en la tabla de posiciones.")

    conn.close()

# Function to show the player's rank
def show_player_rank(update, context):
    user = update.effective_user
    username = user.first_name

    # Create a connection to the database and a cursor
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()

    user_id = get_user_id(username)  # Pass the cursor as an argument
    if user_id:
        cursor.execute('''
            SELECT username, wins, losses,
                (SELECT COUNT(*) + 1
                 FROM players AS p2
                 WHERE p2.wins > p.wins) AS rank
            FROM players AS p
            WHERE user_id = ?
        ''', (user_id,))
        player_info = cursor.fetchone()

        if player_info:
            username, wins, losses, rank = player_info
            update.message.reply_text(f"Posicion de {username} en el torneo: {rank}")
        else:
            update.message.reply_text("Aun no has jugado.")
    else:
        update.message.reply_text("No estas participando en el torneo.")
    cursor.close()
    conn.close()

# Function to increment points for a user and send a private message if they win points
def increment_points_and_notify(update: Update, user_id):
    try:
        # Create a connection to the database and a cursor inside the function
        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE players
            SET points = points + 1  -- Increment points
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

        # Get the updated points for the user
        cursor.execute('SELECT points FROM players WHERE user_id = ?', (user_id,))
        updated_points = cursor.fetchone()[0]

        # Check if the user has won points
        if updated_points > 0:
            # Send a private message to the user
            update.message.reply_text(f'¡Has ganado {updated_points} puntos!')

        # Log the increment
        logging.info(f'Incremented points for user {user_id}')

        # Close the connection after the operation
        conn.close()
    except sqlite3.IntegrityError:
        # Handle integrity error if needed
        pass
    
def show_stats(update, context):
    user = update.effective_user
    username = user.first_name

    # Create a connection to the database and a cursor
    conn = sqlite3.connect('tournament.db')
    cursor = conn.cursor()

    user_id = get_user_id(username)  # Pass the cursor as an argument
    if user_id:
        cursor.execute('''
            SELECT username, wins, losses, points
            FROM players
            WHERE user_id = ?
        ''', (user_id,))
        player_info = cursor.fetchone()

        if player_info:
            username, wins, losses, points = player_info
            update.message.reply_text(f"Estadísticas de {username}:\n"
                                      f"Victorias: {wins}\n"
                                      f"Derrotas: {losses}\n"
                                      f"Puntos ganados en el torneo: {points}")
        else:
            update.message.reply_text("Aun no has jugado en el torneo.")
    else:
        update.message.reply_text("No estas participando en el torneo.")
    cursor.close()
    conn.close()

# Function to ban a player from the tournament by user ID
def tban(update: Update, context: CallbackContext):
    # Check if the user issuing the command is the bot admin
    if update.message.from_user.username == '@lIlllIlIlIIllIlIlIIl':
        user_id_to_ban = context.args[0]  # Get the user ID to ban

        conn = sqlite3.connect('tournament.db')
        cursor = conn.cursor()
        
        # Check if the user is participating in the tournament
        user_to_ban = get_user_id(user_id_to_ban)
        if user_to_ban is not None:
            # Remove the user from the participating_users set
            participating_users.remove(user_to_ban)

            # Get the user_id of the player to ban
            user_id = get_user_id(user_to_ban)
            if user_id is not None:
                # Delete the player from the database
                delete_player(user_id)
                conn.commit()
            cursor.close()
            conn.close()

            update.message.reply_text(f'{user_to_ban} ha sido baneado del torneo.')
        else:
            update.message.reply_text(f'El usuario con ID {user_id_to_ban} no está en el torneo.')
    else:
        update.message.reply_text('No tienes permiso para usar este comando.')
        
# Function to announce a message using the bot
def tannounce(update: Update, context: CallbackContext):
    # Check if the user issuing the command is the bot admin
    if update.message.from_user.username == '@lIlllIlIlIIllIlIlIIl':
        message_to_announce = ' '.join(context.args)  # Get the message to announce

        # Send the message to the configured channel
        if channel_id:
            bot.send_message(chat_id=channel_id, text=message_to_announce)
            update.message.reply_text('Mensaje anunciado con éxito.')
        else:
            update.message.reply_text('El canal de anuncios no está configurado.')
    else:
        update.message.reply_text('No tienes permiso para usar este comando.')

# Function to configure the tournament settings
def tconfig(update: Update, context: CallbackContext):
    # Check if the user issuing the command is the bot admin
    if update.message.from_user.username == '@lIlllIlIlIIllIlIlIIl':
        # Implement your configuration logic here
        update.message.reply_text('Función de configuración en desarrollo.')
    else:
        update.message.reply_text('No tienes permiso para usar este comando.')

# Main function
def main():
    # Create the players table if it does not exist
    create_players_table()

    # Configure the updater and dispatcher
    dispatcher = updater.dispatcher

    # Add handlers to the dispatcher
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, handle_message))
    dispatcher.add_handler(CommandHandler('setchannel', set_channel))
    dispatcher.add_handler(CommandHandler('jointournament', join_tournament))
    dispatcher.add_handler(CommandHandler('leavetournament', leave_tournament))
    dispatcher.add_handler(CommandHandler('leaderboard', show_leaderboard, pass_args=True))
    dispatcher.add_handler(CommandHandler('myrank', show_player_rank))
    dispatcher.add_handler(CommandHandler('stats', show_stats))

    # Start the bot
    updater.start_polling()

    # Run the bot until it stops
    updater.idle()

if __name__ == "__main__":
    main()

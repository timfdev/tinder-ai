from messenger.app.db.database import SessionLocal, init_db
from messenger.app.db.models import Chat, MessageDB


def print_all_items():
    """Fetch and print all items from the database with content."""
    # Initialize the database to ensure tables exist
    init_db()

    # Create a database session
    with SessionLocal() as db:
        # Fetch all conversations
        print("\nTable: conversations")
        chats = db.query(Chat).all()
        if chats:
            for chat in chats:
                print(f"ID: {chat.id}, Match ID: {chat.match_id}, "
                      f"Name: {chat.profile['name']}, Age: {chat.profile['age']}, "
                      f"Last Interaction: {chat.last_interaction}, Ready to Meet: {chat.ready_to_meet}, "
                      f"Readiness Timestamp: {chat.readiness_timestamp}")
        else:
            print("No entries found in conversations.")

        # Fetch all messages
        print("\nTable: messages")
        messages = db.query(MessageDB).all()
        if messages:
            for message in messages:
                print(f"Chat ID: {message.chat_id}, Message: {message.message}, "
                      f"Is Received: {message.is_received} -- {message.timestamp}")
        else:
            print("No entries found in messages.")


if __name__ == "__main__":
    print("Testing database and printing all items...")
    print_all_items()
    print("Done.")

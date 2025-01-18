DB_FILE=messenger/app/db/data/conversations.db

clean-db:
	rm -f $(DB_FILE)
	@echo "Database file $(DB_FILE) removed."

init-db:
	python -m messenger.app.db.database
	@echo "Database initialized."

reset-db: clean-db init-db
	@echo "Database reset completed."

help:
	@echo "Available commands:"
	@echo "  clean-db   - Remove the database file"
	@echo "  init-db    - Initialize the database"
	@echo "  reset-db   - Remove and reinitialize the database"

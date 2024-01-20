import logging


def configure_logging(app, config=None):
    # Configure the logging level and format
    if config:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        app.config['DEBUG'] = True

        # Add a file handler to log to a file
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # Configure a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)

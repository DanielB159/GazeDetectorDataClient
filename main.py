"""Module for running the main function"""
from main_hub import start_main_hub
from imports import dotenv

if __name__ == "__main__":
    dotenv.load_dotenv()
    start_main_hub()

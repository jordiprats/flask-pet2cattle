from flask import Flask

app = Flask(__name__)

from .util import filters
from app import blog
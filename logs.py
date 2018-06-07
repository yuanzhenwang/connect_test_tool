import logging,os
from logging.handlers import RotatingFileHandler


def set_logger(name):
	logger = logging.getLogger(name)
	logger.setLevel(level = logging.DEBUG)

	handler0 = RotatingFileHandler("logs/info.txt",maxBytes = 1*1024*1024*100,backupCount = 2)
	handler0.setLevel(logging.INFO)
	formatter0 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	handler0.setFormatter(formatter0)
	logger.addHandler(handler0)

	handler = RotatingFileHandler("logs/debug.txt",maxBytes = 1*1024*1024*100,backupCount = 2)
	handler.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	handler1 = RotatingFileHandler("logs/error.txt",maxBytes = 1*1024*1024*100,backupCount = 2)
	handler1.setLevel(logging.ERROR)
	formatter1 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler1.setFormatter(formatter1)
	logger.addHandler(handler1)
	return logger	
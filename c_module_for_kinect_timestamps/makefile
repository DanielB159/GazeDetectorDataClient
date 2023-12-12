CC=gcc
CFLAGS=-I"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\include"
LDFLAGS=-L"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\windows-desktop\amd64\release\lib" -lk4a -lk4arecord
SRC=.\timestamp_retrieval.c
OUT=myapp.exe

all:
	$(CC) $(CFLAGS) $(LDFLAGS) $(SRC) -o $(OUT)
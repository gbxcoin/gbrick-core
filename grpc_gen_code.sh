#!/bin/sh
# grpc 를 위한 python 코드를 자동으로 생성한다.

echo "Generating python grpc code from proto...."
echo "into > " $PWD
cd gbrick
python3 -m grpc.tools.protoc -I'./protos' --python_out='./protos' --grpc_python_out='./protos' './protos/gbrick.proto'
cd ..
echo ""

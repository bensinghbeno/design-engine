import 'package:flutter/material.dart';
import 'dart:io';

void main() => runApp(MyApp());
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: Image.file(new File('/storage/emulated/0/Download/blueimage.jpeg')), //   <-- image


      ),
    );
  }
}
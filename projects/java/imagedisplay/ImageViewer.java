import javax.swing.*;
import java.io.*;
import java.awt.event.*;

public class ImageViewer {

 public static void main(String[] args) {
    JFrame frame = new ImageViewerFrame();
    frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
    frame.setExtendedState(JFrame.MAXIMIZED_BOTH); 
    frame.setVisible(true);
 }
}

@SuppressWarnings("serial")

class ImageViewerFrame extends JFrame {
 
 JLabel label;

 public ImageViewerFrame() {   
  label = new JLabel();
  add(label);
  label.setIcon(new ImageIcon("blueim.jpeg"));
}


}

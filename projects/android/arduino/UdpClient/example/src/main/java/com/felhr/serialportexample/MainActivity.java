package com.felhr.serialportexample;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.widget.TextView;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.Date;
import java.util.Enumeration;

import java.lang.ref.WeakReference;
import java.util.Set;

public class MainActivity extends AppCompatActivity implements View.OnClickListener {


    private final static String TAG = MainActivity.class.getSimpleName();

    TextView infoIp, infoPort;
    TextView textViewPrompt;
    EditText editTextIp;
    EditText editTextPort;

    static final int UdpServerPORT = 7777;
    private void updatePrompt(final String prompt) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                textViewPrompt.setText("Data    : " + prompt);
            }
        });
    }

    private String getIpAddress() {
        String ip = "";
        try {
            Enumeration<NetworkInterface> enumNetworkInterfaces = NetworkInterface
                    .getNetworkInterfaces();
            while (enumNetworkInterfaces.hasMoreElements()) {
                NetworkInterface networkInterface = enumNetworkInterfaces
                        .nextElement();
                Enumeration<InetAddress> enumInetAddress = networkInterface
                        .getInetAddresses();
                while (enumInetAddress.hasMoreElements()) {
                    InetAddress inetAddress = enumInetAddress.nextElement();

                    if (inetAddress.isSiteLocalAddress()) {
                        ip += "Device IP : "
                                + inetAddress.getHostAddress() + "\n";
                    }

                }

            }

        } catch (SocketException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            ip += "Something Wrong! " + e.toString() + "\n";
        }

        return ip;
    }


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //UDP///

        editTextIp = (EditText) findViewById(R.id.editTextIp);
        editTextPort = (EditText) findViewById(R.id.editTextPort);

        Button buttonSend = (Button) findViewById(R.id.buttonSend);
        buttonSend.setOnClickListener(this);
        Button buttonSend2 = (Button) findViewById(R.id.buttonSend2);
        buttonSend2.setOnClickListener(this);
        Button buttonSend3 = (Button) findViewById(R.id.buttonSend3);
        buttonSend3.setOnClickListener(this);
        Button buttonSend4 = (Button) findViewById(R.id.buttonSend4);
        buttonSend4.setOnClickListener(this);
    }

    @Override
    public void onClick(View v) {


        String stringIp = editTextIp.getText().toString();
        String stringPort = editTextPort.getText().toString();
        int intPort = Integer.parseInt(stringPort);

        switch (v.getId()) {

            case R.id.buttonSend:
                sendUdpMessage("FORWARD", stringIp, intPort);
                break;
            case R.id.buttonSend2:
                sendUdpMessage("REVERSE", stringIp, intPort);
                break;
            case R.id.buttonSend3:
                sendUdpMessage("LEFT", stringIp, intPort);
                break;
            case R.id.buttonSend4:
                sendUdpMessage("RIGHT", stringIp, intPort);
                break;
        }
    }


        public void sendUdpMessage(final String message, final String strIp, final int intPort) {

            final Handler handler = new Handler();
            Thread thread = new Thread(new Runnable() {


                String stringData;

                @Override
                public void run() {

                    DatagramSocket ds = null;
                    try {
                        ds = new DatagramSocket();
                        // IP Address below is the IP address of that Device where server socket is opened.
                        InetAddress serverAddr = InetAddress.getByName(strIp);
                        DatagramPacket dp;
                        dp = new DatagramPacket(message.getBytes(), message.length(), serverAddr, intPort);
                        ds.send(dp);

                        byte[] lMsg = new byte[1000];
                        dp = new DatagramPacket(lMsg, lMsg.length);
                        ds.receive(dp);
                        stringData = new String(lMsg, 0, dp.getLength());

                    } catch (IOException e) {
                        e.printStackTrace();
                    } finally {
                        if (ds != null) {
                            ds.close();
                        }
                    }

                }
            });

            thread.start();
        }
}

package com.srccodes.android;

import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.app.Activity;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.view.Menu;
import java.io.File;
import android.app.Activity;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.Environment;
import android.util.Log;
import android.widget.ImageView;
import android.widget.Toast;

public class HelloActivity extends Activity {

    private static final int PERMISSION_REQUEST_CODE = 100;

    private static final String BEN = "BEN_LOG";
    ImageView imageView1;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_hello);
        imageView1=(ImageView)findViewById(R.id.imageView1);

        Log.d(BEN, "BEN :: Launched App");

        File dir = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/Download/blueimage.jpeg");
        if (checkPermission()) {
            if (dir.exists()) {
                Log.d(BEN, "BEN :: File Exists - " + dir.toString());
                imageView1.setImageBitmap(BitmapFactory.decodeFile(dir.toString()));

            } else {
                Log.d(BEN, "BEN :: File DOes NOT Exist - " + dir.toString());

                requestPermission(); // Code for permission
            }
        }

//        checkPermission();
//
//        String imagename="blueimage.jpg";
//        String dir = Environment.getExternalStorageDirectory()+File.separator+"Download";
//
//        String filepath = "/data/local/blueimage.jpg";
//        File imagefile = new File(filepath);
//
//        if(imagefile.exists())
//        {
//            Log.d(BEN, "BEN :: File Exists");
//
//            Log.d(BEN, "BEN :: PATH = " + filepath);
//
//            imageView1.setImageBitmap(BitmapFactory.decodeFile(filepath));
//        }
//        else
//        {
//            Log.e("","Image does not exist");
//        }
    }

    private boolean checkPermission() {
        int result = ContextCompat.checkSelfPermission(HelloActivity.this,     android.Manifest.permission.READ_EXTERNAL_STORAGE);
        if (result<= PackageManager.PERMISSION_GRANTED) {
            return true;
        } else {
            return false;
        }
    }
    private void requestPermission() {
        if (ActivityCompat.shouldShowRequestPermissionRationale(HelloActivity.this, android.Manifest.permission.READ_EXTERNAL_STORAGE)) {
            Toast.makeText(HelloActivity.this, "Write External Storage permission allows us to read  files. Please allow this permission in App Settings.", Toast.LENGTH_LONG).show();
        } else {
            ActivityCompat.requestPermissions(HelloActivity.this, new String[] {android.Manifest.permission.READ_EXTERNAL_STORAGE}, PERMISSION_REQUEST_CODE);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String permissions[], int[] grantResults) {
        switch (requestCode) {
            case PERMISSION_REQUEST_CODE:
                if (grantResults.length > 0 && grantResults[0]<= PackageManager.PERMISSION_GRANTED)  {
                Log.e("value", "Permission Granted, Now you can use local drive .");
            } else {
                Log.e("value", "Permission Denied, You cannot use local drive .");
            }
            break;
        }
    }
}

//    @Override
//    protected void onCreate(Bundle savedInstanceState) {
//        super.onCreate(savedInstanceState);
//        setContentView(R.layout.activity_hello);
//    }
//
//    @Override
//    public boolean onCreateOptionsMenu(Menu menu) {
//        // Inflate the menu; this adds items to the action bar if it is present.
//        getMenuInflater().inflate(R.menu.activity_hello, menu);
//        return true;
//    }



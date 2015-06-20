/*
  DigitalReadSerial
 Reads a digital input on pin 2, prints the result to the serial monitor

 This example code is in the public domain.
 */

// digital pin 2 has a pushbutton attached to it. Give it a name:
//int pushButton = 2;

int gpstime = random(100,1000);
int latitude = random(0, 100);
int longitude = random(0,100);
int fixquality = random(-0,1);
int numsats = random(10,16);
int hozaccuracy= random(5,50);
int altitude = random(1000,3000);
int height = altitude + 100;
int timesinceupdate = random(10,1000);
int DGPS = random(1,2);
int checksum =random(0,8);

int exacttime = gpstime;
int energy1 = random(10000,20000);
int energy2 = random(10050,19950);
int altitudereal = altitude + random(-100,100);
int altaccuracy = random(1,100);

int humidity = random (60,70);
int humaccuracy = random (1,20);


int xgrav = random(0,10);
int ygrav = random(0,10);
int zgrav = random(0,10);

int mxgrav = random(0,10);
int mygrav = random(0,10);
int mzgrav = random(0,10);

int tempval1 = random(10,35);
int tempval2 = tempval1 + 1;

int uptime = random(1,1000);

int deviceid = random(1,10000);

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(115200);

  }

// the loop routine runs over and over again forever:
void loop() {
  // read the input pin:
  //int buttonState = digitalRead(pushButton);
  // print out the state of the button:
  Serial.print("{ ");
  Serial.print("    \"gps\": {");
  Serial.print("      \"time\": ");
  Serial.print(gpstime);
  Serial.print(','); 
  Serial.print("      \"latitude\": ");
  Serial.print(latitude);
  Serial.print(','); 
  Serial.print("      \"longitude\": ");
  Serial.print(longitude);
  Serial.print(',');
  Serial.print("      \"quality\": ");
  Serial.print(fixquality);
  Serial.print(',');
  Serial.print("      \"numSatellites\": ");
  Serial.print(numsats);
  Serial.print(',');
  Serial.print("      \"horizontalAccuracy\": ");
  Serial.print(hozaccuracy);
  Serial.print(',');
  Serial.print("      \"altitude\": ");
  Serial.print(altitude);
  Serial.print(',');
  Serial.print("      \"height\": ");
  Serial.print(height);
  Serial.print(',');
  Serial.print("      \"timeSinceUpdate\": ");
  Serial.print(timesinceupdate);
  Serial.print(',');
  Serial.print("      \"dgps\": ");
  Serial.print(DGPS);
  Serial.print(',');
  Serial.print("      \"checksum\": ");
  Serial.print(checksum);
  Serial.print("    },");
  

  Serial.print("    \"timing\": ");
  Serial.print(exacttime);
  Serial.print(','); 
  
  Serial.print("    \"energy\": {");
  Serial.print("      \"channel1\": ");
  Serial.print(energy1);
  Serial.print(',');
  Serial.print("      \"channel2\": ");
  Serial.print(energy2);
  Serial.print("    },");

  Serial.print("    \"altitude\": "); 
  Serial.print(altitudereal);
  Serial.print(",");

  Serial.print("    \"humidity\": "); 
  Serial.print(humidity);
  Serial.print(",");

  Serial.print("    \"gravitationalOrientation\": {"); 
  Serial.print("     \"x\": ");
  Serial.print(xgrav);
  Serial.print(",");
  Serial.print("     \"y\": ");
  Serial.print(ygrav);
  Serial.print(",");
  Serial.print("     \"z\": ");
  Serial.print(zgrav);
  Serial.print("    },");  

  Serial.print("    \"magneticOrientation\": {"); 
  Serial.print("     \"x\": ");
  Serial.print(mxgrav);
  Serial.print(",");
  Serial.print("     \"y\": ");
  Serial.print(mygrav);
  Serial.print(",");
  Serial.print("     \"z\": ");
  Serial.print(mzgrav);
  
  Serial.print("    },");

  Serial.print("    \"temperature\": {"); 
  Serial.print("     \"value1\": ");
  Serial.print(tempval1);
  Serial.print(",");
  Serial.print("     \"value2\": ");
  Serial.print(tempval2);
  
  Serial.print("    },");


  Serial.print("    \"uptime\": "); 
  Serial.print(uptime);
  Serial.print(",");
  
  Serial.print("    \"id\": "); 
  Serial.print(deviceid);
  

  Serial.println("}");

  
  //increment and modify things
  gpstime++;
  exacttime++;
  energy1= energy1 + random(-100,100);
  energy2= energy2 + random(-100,100);
  altitudereal = altitudereal + random(-10,10);
  humidity=random(60,70);
  uptime++;
  
  delay(1000);        // delay in between reads for stability
}



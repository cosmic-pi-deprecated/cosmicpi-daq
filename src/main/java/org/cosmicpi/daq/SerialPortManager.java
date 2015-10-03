package org.cosmicpi.daq;

import gnu.io.CommPortIdentifier;
import gnu.io.SerialPort;
import gnu.io.SerialPortEvent;
import gnu.io.SerialPortEventListener;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.TooManyListenersException;

/**
 * Created by jsalmon on 19/06/15.
 */
@Component
public class SerialPortManager implements SerialPortEventListener {

  SerialPort serialPort;
  /**
   * The port we're normally going to use.
   */
  private static final String PORT_NAMES[] = {
      "/dev/tty.usbmodemfa131", // Mac OS X
      "/dev/ttyACM0", // Raspberry Pi
      "/dev/ttyUSB0", // Linux
      "COM3", // Windows
  };
  /**
   * A BufferedReader which will be fed by a InputStreamReader
   * converting the bytes into characters
   * making the displayed results codepage independent
   */
  private BufferedReader input;
  /**
   * The output stream to the port
   */
  private OutputStream output;
  /**
   * Milliseconds to block while waiting for port open
   */
  private static final int TIME_OUT = 2000;
  /**
   * Default bits per second for COM port.
   */
  private static final int DATA_RATE = 115200;

  List<CosmicEventListener> listeners = new ArrayList<>();

  public SerialPortManager() {
    initialize();
  }

  public void initialize() {
    // the next line is for Raspberry Pi and
    // gets us into the while loop and was suggested here was suggested http://www.raspberrypi.org/phpBB3/viewtopic.php?f=81&t=32186
    // System.setProperty("gnu.io.rxtx.SerialPorts", "/dev/ttyACM0");

    CommPortIdentifier portId = null;
    Enumeration portEnum = CommPortIdentifier.getPortIdentifiers();

    //First, Find an instance of serial port as set in PORT_NAMES.
    while (portEnum.hasMoreElements()) {
      CommPortIdentifier currPortId = (CommPortIdentifier) portEnum.nextElement();
      for (String portName : PORT_NAMES) {
        if (currPortId.getName().equals(portName)) {
          portId = currPortId;
          break;
        }
      }
    }
    if (portId == null) {
      System.out.println("Could not find COM port.");
      return;
    }

    try {
      // open serial port, and use class name for the appName.
      serialPort = (SerialPort) portId.open(this.getClass().getName(),
          TIME_OUT);

      // set port parameters
      serialPort.setSerialPortParams(DATA_RATE,
          SerialPort.DATABITS_8,
          SerialPort.STOPBITS_1,
          SerialPort.PARITY_NONE);

      // open the streams
      input = new BufferedReader(new InputStreamReader(serialPort.getInputStream()));
      output = serialPort.getOutputStream();

      // add event listeners
      serialPort.addEventListener(this);
      serialPort.notifyOnDataAvailable(true);
    } catch (Exception e) {
      System.err.println(e.toString());
    }
  }

  interface CosmicEventListener {
    public void onEvent(String line);
  }

  public void addEventListener(CosmicEventListener listener) {
    listeners.add(listener);
  }

  /**
   * This should be called when you stop using the port.
   * This will prevent port locking on platforms like Linux.
   */
  @PreDestroy
  public synchronized void close() {
    if (serialPort != null) {
      serialPort.removeEventListener();
      serialPort.close();
    }
  }

  /**
   * Handle an event on the serial port. Read the data and print it.
   */
  public synchronized void serialEvent(SerialPortEvent event) {
    if (event.getEventType() == SerialPortEvent.DATA_AVAILABLE) {
      try {
        String inputLine = input.readLine();

        for (CosmicEventListener listener : listeners) {
          listener.onEvent(inputLine);
        }

      } catch (IOException e) {
        System.err.println(e.toString());
      }
    }
  }
}

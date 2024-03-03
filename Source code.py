import RPi.GPIO as GPIO
import time
from picamera import PiCamera
from time import sleep
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient  #import azure customission pattern
ENDPOINT='https://southcentralus.api.cognitive.microsoft.com/'
predictor = CustomVisionPredictionClient('045f05ba24584edba0c5716748825ecd', endpoint=ENDPOINT)


belt_motor= 13        #assaign pins
camera = PiCamera()
servoPIN = 17
proximity_sensor1 = 24
proximity_sensor2 = 25
#stepper
steppin= 22
dirpin = 27
GPIO_TRIGGER = 20
GPIO_ECHO = 16

GPIO.setmode(GPIO.BCM)       #initialize setup
GPIO.setwarnings(False)
GPIO.setup(belt_motor, GPIO.OUT)
GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setup(proximity_sensor1,GPIO.IN)
GPIO.setup(proximity_sensor2,GPIO.IN)
GPIO.setup(steppin, GPIO.OUT)
GPIO.setup(dirpin, GPIO.OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

pwm = GPIO.PWM(servoPIN, 50) #supply 50Hz PWM signals to the servo
pwm.start(7.5)

p=GPIO.PWM(belt_motor,30)     #supply 30Hz PWM signals to the servo

def setAngle(angle):        #making servo rotating for the given angle
        duty = angle / 18 + 3
        pwm.ChangeDutyCycle(duty)
        time.sleep(1)



def stepper(stepcount):        #running the steppr motor for a given number of steps
    if stepcount<0:
        stepcount=-1*stepcount
        GPIO.output(dirpin,GPIO.LOW)
    else:
        GPIO.output(dirpin,GPIO.HIGH)
    for s in range(stepcount+1):
        GPIO.output(steppin,GPIO.HIGH)
        time.sleep(0.05/stepspeed)
        GPIO.output(steppin,GPIO.LOW)
        time.sleep(0.05/stepspeed)

def distance():         #function for the finding distance using ultrasonic sensor
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

stepspeed=100      
mystepcount=-4500
gate_position=0
#setAngle(90)


while True:       #executing the main code
    p.start(0)
    p.ChangeDutyCycle(40)#belt is going
    time.sleep(0.5)
    if __name__ == '__main__':
        try:                         #checking for a object
            dist = distance()
            print ("Measured Distance = %.1f cm" % dist)
            time.sleep(0.003)
            if ((dist>0and dist<17)or dist>=1000):
                print(1)
                p.stop()#belt should be stopped
                camera.start_preview()       #capturing the image
                sleep(5)
                camera.capture('/home/pi/Desktop/image.jpg')
                camera.stop_preview()
                with open("/home/pi/Desktop/" + "image.jpg", "rb") as image_contents:        #transfering the image to the image processing training modules
                    results = predictor.classify_image('73dc6476-5383-4f6e-9ffd-5b7f49d500e5', 'Iteration1', image_contents.read())
                for prediction in results.predictions:
                    if prediction.tag_name=='potato':
                        if prediction.probability> 0.5:
                            print("potato")
                            #stepper
                            if gate_position==1:
                                stepper(mystepcount)
                                time.sleep(1)
                                gate_position=0
                            setAngle(45) #servo
                            #belt
                            p.start(0)
                            p.ChangeDutyCycle(50)#belt is going
                            time.sleep(5)
                               
                            if GPIO.input(proximity_sensor1):
                                print ("proxi=1")
                                while GPIO.input(proximity_sensor1):
                                    time.sleep(0.01)
                               
                                setAngle(90)
                            #proxi 1
                        elif prediction.probability<0.5:
                            print("onion")
                            #stepper
                            if gate_position==0:
                                stepper(4500)
                                time.sleep(1)
                                gate_position=1
                            setAngle(123)#servo
                            #belt
                            p.start(0)
                            p.ChangeDutyCycle(50)#belt is going
                            time.sleep(5)
                           
                            if GPIO.input(proximity_sensor2):
                                print ("proxi=2")
                                while GPIO.input(proximity_sensor2):
                                    time.sleep(0.01)
                                setAngle(90)#proxi 2
            else:
                continue
        except KeyboardInterrupt:
            print("Measurement stopped by User")
            GPIO.cleanup()
       
GPIO.cleanup()

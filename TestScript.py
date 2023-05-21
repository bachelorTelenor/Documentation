import meraki
import os
from dotenv import load_dotenv
from datetime import datetime
import customtkinter
import csv


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

running = False
newrun = True
testlog = ""
updated = True
lastUpdateTime = ""
direction = "North"

# Loads variables from .env file
load_dotenv()
API_KEY = os.getenv('MERAKI_API_KEY')
# Variables for connection to Meraki API
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)
organization_id = os.getenv('MERAKI_ORG_ID')

# Gets data from the Meraki API
def getmerakidata():
    response = \
        dashboard.cellularGateway.getOrganizationCellularGatewayUplinkStatuses(
        organization_id, total_pages='all'
    )
    return response

# Used to check if the Meraki update time has updated
def checkupdate(time, newtime):
    if time == newtime:
        return False
    else:
        return True

# Creates the log file
def cretecsv():
    logTime = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")
    testLog = f"TestLog{logTime}"
    csvHeader = ['APIQuery', 'APIUpdate', 'rsrp', 'rsrq', 'MerakiDirection']
    f = open(f"./{testLog}.csv", 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(csvHeader)
    f.close()
    return testLog


class App(customtkinter.CTk):
    # Creates the GUI for the application
    def __init__(self):
        super().__init__()

        self.geometry("500x300")
        self.title("Meraki data")
        self.minsize(900, 400)

        # create 2x2 grid system
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.label = customtkinter.CTkLabel(master=self,
                                            font=customtkinter.CTkFont(size=18),
                                            text="Stopped")
        self.label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 0),
                        sticky="nsew")

        global direction

        self.labelDir = customtkinter.CTkLabel(master=self,
                                               font=customtkinter.CTkFont(size=18),
                                               text="North")
        self.labelDir.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.button = customtkinter.CTkButton(master=self, text="Turn",
                                              command=self.turn,
                                              font=customtkinter.CTkFont(size=18))
        self.button.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        self.textbox = customtkinter.CTkTextbox(master=self,
                                                font=customtkinter.CTkFont(size=18))
        self.textbox.grid(row=2, column=0, columnspan=2, padx=20, pady=(20, 0),
                          sticky="nsew")

        self.button = customtkinter.CTkButton(master=self, text="Start",
                                              command=self.start,
                                              font=customtkinter.CTkFont(size=18),
                                              fg_color="green")
        self.button.grid(row=3, column=1, padx=20, pady=20, sticky="ew")

        self.button = customtkinter.CTkButton(master=self, text="Stop",
                                              command=self.stop,
                                              font=customtkinter.CTkFont(size=18),
                                              fg_color="darkred")
        self.button.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

    # Main function that gets the data from the API and write it to the log if
    # the API is updated
    # Runs every second
    def getdata(self):
        global running
        global newrun
        global testlog
        global updated
        global newUpdate
        global lastUpdateTime
        global direction
        # Runs if start is pressed in the GUI
        if running:
            # Runs the first loop after pressing start to create the log file
            # for the test
            if newrun:
                testlog = cretecsv()
                newrun = False
            # If the data from the API is updated, write it to the GUI and log file
            if updated:
                updated = False
                # Get the data from API
                merakiData = getmerakidata()
                lastUpdateTime = merakiData[0]["lastReportedAt"]
                currentTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                rsrp = merakiData[0]["uplinks"][0]["signalStat"]["rsrp"]
                rsrq = merakiData[0]["uplinks"][0]["signalStat"]["rsrq"]

                # Writes to logfile
                csvRow = [currentTime, lastUpdateTime, rsrp, rsrq, direction]
                f = open(f"./{testlog}.csv", 'a', newline='')
                writer = csv.writer(f)
                writer.writerow(csvRow)
                f.close()

                newUpdate = f"API Query: {currentTime} | API update: " \
                            f"{lastUpdateTime} | rsrp: {rsrp} | rsrq: " \
                            f"{rsrq} | Direction: {direction}"
                # Writes the data to the GUI
                self.textbox.insert("0.0", f"{newUpdate}\n\n")
            # Loops to check if the API data is updated
            if not updated:
                app.update()
                merakiUpdate = getmerakidata()
                updateTime = merakiUpdate[0]["lastReportedAt"]
                updated = checkupdate(lastUpdateTime, updateTime)
        app.after(1000, self.getdata)

    # Function for the start button. Starts the test
    def start(self):
        global running
        running = True
        self.label.configure(text="Running")

    # Function for the stop button. Stops the test
    def stop(self):
        global running
        global newrun
        running = False
        newrun = True
        self.label.configure(text="Stopped")

    # Function for the turn button. Change driving direction for the test
    def turn(self):
        global direction
        if direction == "North":
            direction = "South"
            self.labelDir.configure(text="South")
        else:
            direction = "North"
            self.labelDir.configure(text="North")


if __name__ == "__main__":
    app = App()
    app.after(1000, app.getdata())
    app.mainloop()

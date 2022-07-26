from ast import Try
import sys  # For filesystem functions
import re  # For regex
import time  # For timing
from datetime import datetime
import csv

"""
    Regular Expressions required to find strings in the log file
"""
reBatchRunStartTime = "(?<=Batch Start Date_Time ).*"
reBatchRunEndTime = "(?<=Batch End Date_Time ).*"

# Batch Entry Start
reIsStartTimestampLine = "(?:Batch [A-Z]{3,15}[0-9]{0,4} Start Timestamp: )"
reBatchInStartTimeStampLine = "(?<=Batch ).*(?= Start Timestamp:)"
reTimeStampInStartTimeStampLine = "(?<= Start Timestamp: ).*"

# Batch Entry End
reIsEndTimestampLine = "(?:Batch [A-Z]{3,15}[0-9]{0,4} End Timestamp: )"
reBatchInEndTimeStampLine = "(?<=Batch ).*(?= End Timestamp:)"
reTimeStampInEndTimeStampLine = "(?<= End Timestamp: ).*"

# Batch Entry Status
reIsBatchStatusLine = "(?:Batch [A-Z]{3,15}[0-9]{0,4}  completed Successfully|Batch [A-Z]{3,15}[0-9]{0,2} Timed Out|Batch [A-Z]{3,15}[0-9]{0,2} Failed)"
reBatchInStatusLine = "(?<=Batch ).*(?=  completed Successfully| Timed Out| Failed)"
reStatusInStatusLine = "(completed Successfully|Timed Out|Failed)"

#############################################################################################


def calculateElapsedTime(startTime, endTime):
    startDT = getDateFromString(startTime.split(".")[0])
    endDT = getDateFromString(endTime.split(".")[0])

    dateDiff = endDT - startDT

    # print(f"Difference = {dateDiff}")
    # minutes = divmod(dateDiff.total_seconds(), 60)
    # print("Total difference in minutes: ", minutes[0], "minutes", minutes[1], "seconds")
    # minutes = divmod(dateDiff.seconds, 60)
    # print("Total difference in minutes: ", minutes[0], "minutes", minutes[1], "seconds")

    return dateDiff


def getDateFromString(strDate):
    return datetime.strptime(strDate, "%Y%m%d_%H%M%S")


def main():
    startTime = time.perf_counter()

    lines = []
    listOfBatches = []
    batchEntry = {}
    selectedBatch = {}

    lineNumber = 0
    with open(inFile) as f:
        for line in f:
            lineNumber += 1
            # print(f"Processing line: {lineNumber}")
            if (
                re.search(reBatchRunStartTime, line) is not None
            ):  # Batch run start indicator
                lines.append(line.strip("\n"))
            elif (
                re.search(reIsStartTimestampLine, line) is not None
            ):  # Batch item start time
                # This should always be the 1st time a specific batch item name is found
                # Create a list item for this batch
                batchEntry = {}
                batchEntry["Name"] = re.search(reBatchInStartTimeStampLine, line).group(
                    0
                )
                batchEntry["Start Time"] = re.search(
                    reTimeStampInStartTimeStampLine, line
                ).group(0)
                batchEntry["End Time"] = ""
                batchEntry["Elapsed Time"] = ""
                batchEntry["Status"] = ""
                listOfBatches.append(batchEntry)
                print(f"Processing line: {lineNumber}")
                print(f"Batch entry: {batchEntry}")
                # Add the Name and the Start Time to a directory
                lines.append(line.strip("\n"))
            elif re.search(reIsBatchStatusLine, line) is not None:
                # Find the correct entry in the directory
                batchName = re.search(reBatchInStatusLine, line).group(0)
                ## print(f"batchName = {batchName}")
                ## An error will be thrown if the batch start was not found
                try:
                    selectedBatch = next(
                        filter(
                            lambda selectedBatch: selectedBatch.get("Name")
                            == batchName,
                            listOfBatches,
                        )
                    )
                    # Add the Status
                    selectedBatch["Status"] = re.search(
                        reStatusInStatusLine, line
                    ).group(0)
                    lines.append(line.strip("\n"))
                except:
                    print(
                        f"\n####################\n{batchName} start Time not found in file, so this entry is NOT added to the list of batches\n####################\n"
                    )
            elif re.search(reIsEndTimestampLine, line) is not None:
                # Find the correct entry in the directory
                batchName = re.search(reBatchInEndTimeStampLine, line).group(0)
                try:
                    selectedBatch = next(
                        filter(
                            lambda selectedBatch: selectedBatch.get("Name")
                            == batchName,
                            listOfBatches,
                        )
                    )
                    selectedBatch["End Time"] = re.search(
                        reTimeStampInEndTimeStampLine, line
                    ).group(0)
                    selectedBatch["Elapsed Time"] = calculateElapsedTime(
                        selectedBatch["Start Time"], selectedBatch["End Time"]
                    )
                    # Add the End Time
                    lines.append(line.strip("\n"))
                except:
                    # This exception can be ignored - entry not in list
                    pass

            elif (
                re.search(reBatchRunEndTime, line) is not None
            ):  # Batch run end indicator
                lines.append(line.strip("\n"))

    endTime = time.perf_counter()
    print(f"In {endTime - startTime:0.4f} seconds")

    headStr = "Name,Start Time, End Time, Elapsed Time, Status"
    print(headStr)
    for batch in listOfBatches:
        outStr = ""
        for item in batch:
            outStr = outStr + str(batch[item]) + ","
        print(outStr)

    csv_columns = ["Name", "Start Time", "End Time", "Elapsed Time", "Status"]
    csv_file = sys.argv[1].split(".")[0] + ".CSV"
    try:
        with open(csv_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for batch in listOfBatches:
                writer.writerow(batch)
    except:
        print("Error writing file")


if __name__ == "__main__":

    # Check the command line parameters and set variables
    if len(sys.argv) != 2:
        print(
            f"Invalid syntax for running this utility: \
                Please use - {sys.argv[0]} InputFile"
        )
        sys.exit()
    else:
        print(f"Processing {sys.argv[1]} as input.")
        inFile = sys.argv[1]  # "BaNCS_NFR-20210901_221001.txt"
        main()

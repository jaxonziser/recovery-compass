def main():
    duration_submitted=input("State Workout Duration in Minutes: ")
    exertion_submitted=input("State Exertion Level (1-10): ")
    duration_calculated=float(duration_submitted)
    exertion_calculated=float(exertion_submitted)
    print()
    print("Session Summary: " )
    print()
    print("Your Workout Duration is: " + str(duration_calculated) + " minutes")
    print("Your Exertion Level is: " + str(exertion_calculated) + "/10")
    print("Your Calculated Session Load is: " + str((duration_calculated) * (exertion_calculated)))
    print()

main()
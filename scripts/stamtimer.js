<script>
    // Calculate 100 days from now
    let countdownDate = new Date();
    countdownDate.setDate(countdownDate.getDate() + 100); // Adds 100 days

    // Update the countdown every 1 second
    let countdownInterval = setInterval(function() {
        let now = new Date().getTime();
        let distance = countdownDate - now;

        // Time calculations for days, hours, minutes, and seconds
        let days = Math.floor(distance / (1000 * 60 * 60 * 24));

        // Output the result in the element with id="days"
        document.getElementById("days").innerHTML = days;

        // If the countdown is finished, display the message
        if (distance < 0) {
            clearInterval(countdownInterval);
            document.querySelector(".header__content-timer-time").innerHTML = "SUCCESSFULLY STARTED!";
        }
    }, 1000);
</script>
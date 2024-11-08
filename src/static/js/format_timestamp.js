function formatTimestamp(isoTimestamp) {
    const now = new Date();
    const timestamp = new Date(isoTimestamp);
    const diffInSeconds = Math.floor((now - timestamp) / 1000);

    // If invalid date, return original string
    if (isNaN(timestamp.getTime())) {
        return isoTimestamp;
    }

    // Less than 1 minute ago
    if (diffInSeconds < 60) {
        return 'Just now';
    }

    // Less than 1 hour ago
    if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    }

    // Less than 24 hours ago
    if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    }

    // More than 24 hours ago - show date
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
    };
    return timestamp.toLocaleDateString('en-US', options);
}
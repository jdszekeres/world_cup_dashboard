class DataFormatter:
    def __init__(self, data):
        self.data = data

    def get_country_logo(self, match):
        """Extract country logo URL from match data"""
        try:
            if not match or match == {}:
                return None, None
            competitors = match.get("competitions", [])[0].get("competitors", [])
            if competitors:
                return competitors[0].get("team", {}).get("logo"), competitors[1].get("team", {}).get("logo")
        except Exception as e:
            print(f"Error extracting country logo: {e}")
        return None, None
    
    def get_country_name(self, match):
        """Extract country name from match data"""
        try:
            if not match or match == {}:
                return None, None
            competitors = match.get("competitions", [])[0].get("competitors", [])
            if competitors:
                return competitors[0].get("team", {}).get("displayName"), competitors[1].get("team", {}).get("displayName")
        except Exception as e:
            print(f"Error extracting country name: {e}")
        return None, None
    
    def get_score(self, match):
        """Extract score from match data"""
        try:
            if not match or match == {}:
                return None, None
            competitors = match.get("competitions", [])[0].get("competitors", [])
            if competitors:
                return competitors[0].get("score"), competitors[1].get("score")
        except Exception as e:
            print(f"Error extracting score: {e}")
        return None, None
    
    def get_time(self, match):
        """Extract time from match data"""
        try:
            if not match or match == {}:
                return None
            status = match.get("status", {})
            if status:
                return status.get("displayClock", "")
        except Exception as e:
            print(f"Error extracting time: {e}")
        return None
    
    def get_event_details(self, event):
        """Extract event details from event data"""
        try:
            if not event or event == {}:
                return None
            name = event.get("type", {}).get("name", "")
            is_scoring_play = event.get("scoringPlay", False)
            athletes = ", ".join(
                athlete.get("displayName", "")
                for athlete in event.get("athletesInvolved", [])
                if athlete.get("displayName", "")
            )
            return {"name": self._pretty_print_event(name), "is_scoring_play": is_scoring_play, "athletes": athletes}
        except Exception as e:
            print(f"Error extracting event name: {e}")
        return None
    def get_status(self, match):
        """Extract status from match data"""
        try:
            if not match or match == {}:
                return None
            status = match.get("status", {})
            if status:
                return self._pretty_print_event(status.get("type", {}).get("name", ""))
        except Exception as e:
            print(f"Error extracting status: {e}")
        return None
    def get_status_change_text(self, status):
        """Convert status change to user-friendly text"""
        try:
            if not status or status == None:
                return ""
            if "Halftime" in status:
                return "Halftime"
            elif "Full Time" in status:
                return "Full Time"
            elif "In Progress" in status:
                return "In Progress"
            else:
                return self._pretty_print_event(status)
        except Exception as e:
            print(f"Error formatting status change text: {e}")
        return ""
    def _pretty_print_event(self, event):
        """Helper function to pretty print event data for debugging"""
        if not event:
            return ""
        
        # Convert camelCase or snake_case to Title Case
        event = event.replace("_", " ")
        event = ''.join([' ' + c if c.isupper() else c for c in event]).strip()
        return event.title()
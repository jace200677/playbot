using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System;

[Serializable]
public class NOAAAlert
{
    public string eventName;
    public string area;
    public int severity;
}

public class NOAAAlerts : MonoBehaviour
{
    public List<NOAAAlert> alerts = new List<NOAAAlert>();

    // Call this every 30 seconds
    public void FetchAlerts()
    {
        StartCoroutine(FetchCoroutine());
    }

    IEnumerator FetchCoroutine()
    {
        using (UnityWebRequest www = UnityWebRequest.Get("https://api.weather.gov/alerts/active"))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning("NOAA fetch failed: " + www.error);
                yield break;
            }

            var json = www.downloadHandler.text;
            var data = JsonUtility.FromJson<Wrapper>(json);

            alerts.Clear();
            foreach (var feature in data.features)
            {
                string evt = feature.properties.eventName;
                if (!string.IsNullOrEmpty(evt))
                {
                    alerts.Add(new NOAAAlert
                    {
                        eventName = evt,
                        area = feature.properties.areaDesc,
                        severity = GetPriority(evt)
                    });
                }
            }

            // Sort by severity
            alerts.Sort((a,b) => b.severity.CompareTo(a.severity));
        }
    }

    int GetPriority(string evt)
    {
        switch(evt)
        {
            case "Tornado Emergency": return 100;
            case "Tornado Warning": return 95;
            case "Severe Thunderstorm Warning": return 80;
            case "Flash Flood Warning": return 75;
            case "Tornado Watch": return 60;
            case "Severe Thunderstorm Watch": return 50;
            default: return 0;
        }
    }

    [Serializable]
    private class Wrapper
    {
        public Feature[] features;
    }

    [Serializable]
    private class Feature
    {
        public Properties properties;
    }

    [Serializable]
    private class Properties
    {
        public string eventName;
        public string areaDesc;
    }
}

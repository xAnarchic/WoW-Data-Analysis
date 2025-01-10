# WoW-Data-Analysis
Data analysis project on World of Warcraft raiding data.

This project aims to analyse the performance of a guild (a collection of players under the same team name) using a variety of different metrics. These metrics were pulled from the publicly available API (v2) on WarcraftLogs. This data was analysed to determine potential recommendations that may improve overall team execution in a particular raid (an in-game dungeon where players work together to defeat challenging NPCs).  

Technology used: GraphQL, Python, SQL, Power Bi. 


I utilised Python to: query data from a publicly available API via GraphQL that hosts World of Warcraft raiding data, clean and organise the data, and then import the data into MySqlWorkbench. I leveraged SQL to perform further cleaning of the imported data, as well as create novel IDs to correspond with each player name in the dataset. Lastly, I used Power Bi to visualise the data imported from MySQLWorkbench where the use of IDs avoided player name duplication. This enabled me to improve visualisation performance in Power Bi.


Examples of visualisations:

[ReportScreenshot.pdf](https://github.com/user-attachments/files/18295411/ReportScreenshot.pdf)

[ReportSnippet.pdf](https://github.com/user-attachments/files/18295406/ReportSnippet.pdf)




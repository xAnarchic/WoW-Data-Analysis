# WoW-Data-Analysis
Data analysis project on World of Warcraft raiding data.

This project aims to analyse the performance of a guild (a collection of players under the same team name) using a variety of different metrics. These metrics were pulled from the publicly available API (v2) on WarcraftLogs. This data was analysed to determine potential recommendations that may improve overall guild execution in a particular raid (an in-game dungeon where players work together to defeat challenging NPCs).  

Technology used: GraphQL, Python, SQL, Power BI. 


I utilised Python to: query data from a publicly available API via GraphQL that hosts World of Warcraft raiding data, clean and organise the data, and then import the data into MySqlWorkbench. I leveraged SQL to perform further cleaning of the imported data, as well as create novel IDs to correspond with each player name in the dataset. Lastly, I used Power BI to visualise the data imported from MySQLWorkbench where the use of IDs avoided player name duplication. This enabled me to improve visualisation performance in Power BI.


Examples of visualisations:

[ReportScreenshotAQ40.pdf](https://github.com/xAnarchic/WoW-Data-Analysis/blob/42176dc2d184a1aa0b83fc22b1892dd37efdb6b2/Report%20screenshots/guildreportsAQprax.pdf)

[ReportScreenshotBWL.pdf](https://github.com/xAnarchic/WoW-Data-Analysis/blob/42176dc2d184a1aa0b83fc22b1892dd37efdb6b2/Report%20screenshots/guildreportsBWLzomb.pdf)

[ReportSnippet.pdf](https://github.com/xAnarchic/WoW-Data-Analysis/blob/42176dc2d184a1aa0b83fc22b1892dd37efdb6b2/Report%20screenshots/ReportSnippet.pdf)


The analysis uses data from the raid zone "Temple of Ahn'Qiraj", but users can also retrieve and visualise data from "Blackwing's Lair". Only guild data from the "Season of Discovery" version of Classic World of Warcraft should be used. Guild names and IDs can be found on the Warcraft Logs website: https://sod.warcraftlogs.com/ 

A client id and secret can be created here: https://www.warcraftlogs.com/api/clients/ 





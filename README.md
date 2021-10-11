# lds-conference-analysis

This repository contains Python code for analyzing historical text of addresses
given at the twice-yearly general conferences held by the Church of Jesus Christ
of Latter-day Saints. There is currently an online resource for searching text of
all talks going back to the 1850s at
[lds-general-conference.org](https://www.lds-general-conference.org/). It is a
very useful resource, and perhaps the easiest to use for many research projects.
This Python repository is for those wishing to do more detailed analysis that
requires direct access to full texts.


## Sources
As the full text of the general conference addresses are presumed to be copyrighted,
this repository does not include them. Instead, it includes scripts for downloading
them from published online sources. Text of talks are currently available in the
following places:
 * The church's own web site
 ([churchofjesuschrist.org](https://www.churchofjesuschrist.org/general-conference)).
 This includes talks going back to 1971.
 * [scriptures.byu.edu](https://scriptures.byu.edu/#::g). The BYU-hosted scriptures
 site includes full text of talks from 1942 up to the present day. After each new
 general conference, it eventually gets updated, but not as quickly as the church's
 web site.
 * [archive.org](https://archive.org/details/conferencereport). These are scans of
 Conference Report that have been published to archive.org by the church history
 library and cover years from roughly 1897 to the present. Text downloads are
 available, but they are automatically generated using OCR (optical character
 recognition) and thus prone to error, plus they do not have authors and references
 tagged in the way that the other sources do. Converting these to a format useful
 for the Python scripts in this repository will take some additional work and is a
 future project.
 * The [Journal of Discourses](https://en.wikisource.org/wiki/Journal_of_Discourses)
 contains various sermons from the 19th century and is available from a variety
 of sources since it's old enough to all be public domain at this point. At some
 point I may incorporate these texts into the repository.

## Code usage

A Jupyter notebook containing examples of how to run the downloaders and use the
libraries to analyze text can be found in the document
[Using the Python libraries](https://nbviewer.jupyter.org/github/qhspencer/lds-conference-analysis/blob/master/Using%20the%20Python%20libraries.ipynb).

## Results


## Other files
* search_data.json: a set of example searches that may be of interest
* run_text_searches.py: a script that loads the contents of search_data.json
 and creates a plot for each search.
* sunstone2020.py: a script I used for creating my charts presented in my
 presentation at the 2020 Sunstone Symposium.

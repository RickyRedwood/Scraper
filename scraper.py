from selenium import webdriver
from selenium.webdriver.support.ui import Select
import requests
import os
from bs4 import BeautifulSoup
from datetime import date
from datetime import timedelta
from class_structure import *
import csv


def calcnumpages(numrecs):
    numpages = numrecs // 20
    if numrecs % 20 == 0:
        numpages = numpages - 1
    return numpages + 1


def combinefiles(outputfiles):
    with open('data.txt', 'w') as g:
        for county in outputfiles.keys():
            inputfile = 'RAW ' + outputfiles[county] + '.txt'
            with open(inputfile, 'r') as f:
                print('Adding ' + inputfile + ' to data.txt')
                for line in f:
                    g.write(line)
    deletefiles(outputfiles)


def createfiles(outputfiles):
    for county in outputfiles.keys():
        outputfile = 'RAW ' + outputfiles[county] + '.txt'
        f = open(outputfile, 'w')
        f.close()


def deletefiles(f):
    for county in f.keys():
        fname = 'RAW ' + f[county] + '.txt'
        os.remove(fname)


def getData(driver, f, county, lookup, bm, bd, by, em, ed, ey):
    driver.get(lookup)
    driver.find_element_by_link_text("Advanced Options").click()
    driver.find_element_by_id("cmbMonth1").click()
    Select(driver.find_element_by_id("cmbMonth1")).select_by_visible_text(bm)
    driver.find_element_by_id("cmbMonth1").click()
    driver.find_element_by_id("cmbDay1").click()
    Select(driver.find_element_by_id("cmbDay1")).select_by_visible_text(bd)
    driver.find_element_by_id("cmbDay1").click()
    driver.find_element_by_id("cmbYear1").click()
    Select(driver.find_element_by_id("cmbYear1")).select_by_visible_text(by)
    driver.find_element_by_id("cmbYear1").click()
    driver.find_element_by_id("cmbMonth2").click()
    Select(driver.find_element_by_id("cmbMonth2")).select_by_visible_text(em)
    driver.find_element_by_id("cmbMonth2").click()
    driver.find_element_by_id("cmbDay2").click()
    Select(driver.find_element_by_id("cmbDay2")).select_by_visible_text(ed)
    driver.find_element_by_id("cmbDay2").click()
    driver.find_element_by_id("cmbYear2").click()
    Select(driver.find_element_by_id("cmbYear2")).select_by_visible_text(ey)
    driver.find_element_by_id("cmbYear2").click()
    driver.find_element_by_id("btnSubmit3").click()
    numrecs = driver.find_element_by_class_name('text-heading')
    numrecs = int(numrecs.text.split()[0])
    numpages = calcnumpages(numrecs)
    for x in range(1, numpages + 1):
        page = driver.page_source
        if x == 1:
            pass
        elif x >= 2 and x <= 10:
            driver.find_element_by_link_text(str(x)).click()
        else:
            raise ValueError('Page has too many entries to read properly')
        page = driver.page_source
        scrape(f, page, county)


def getDateRange():
    print('Enter dates as mmddyyyy')
    startday = input('Enter beginning date: ')
    finishday = input('   Enter ending date: ')
    startday = date(int(startday[-4:]), int(startday[:2]), int(startday[2: 4]))
    finishday = date(int(finishday[-4:]), int(finishday[:2]), int(finishday[2: 4]))
    return startday, finishday


def scrape(f, page, county):
    #r = requests.get(url)
    soup = BeautifulSoup(page, 'lxml')
    table = soup.table  # find the table references
    reclist = []

    with open(f, 'a', newline='') as outfile:
        if table is None:
            pass
        else:
            for br in table.find_all('br'):  # finds the <br> and replaces with newlines (for the names)
                br.replace_with('\n')

            table_rows = table.find_all('tr')  # returns a list of table rows
            for tr in table_rows:
                td = tr.find_all('td')  # finds the table data
                row = [i.text for i in td]  # returns a list of data in each row from NDO. row is type list.
                if len(row) == 5:
                    row.append(county)
                    if row[0][-9:].strip() == 'Replatted':
                        note = '(Replatted)'
                        row[0] = row[0][-20:-10].strip()
                    else:
                        row[0] = row[0][-10:].strip()
                        note = ''
                    row[1] = row[1].strip()
                    row[2] = row[2].strip()
                    row[3] = row[3].strip()
                    # PropertyRecord(county, date, deedtype, legaldesc, grantor, grantee)
                    proprec = PropertyRecord(row[5], row[0], row[4],
                                             row[1].split('\n'), row[2].split('\n'), row[3].split('\n'))
                    if note != '':
                        proprec.addnote(note)
                    reclist.append(proprec)
                    writeoutputfile(outfile, proprec)


def writeoutputfile(f, fobj):
    # TODO get rid of quotes in legals and multi-party grantors/ees
    # using tabs as the delimiter in the file
    # the [2:-2] in getlegal(), getgrantor(), and getgrantee() get rid of the brackets from being
    # a list
    f.write(str(fobj.getdate()) + '\t' +
            str(fobj.getcounty()) + '\t' +
            str(fobj.getdeedtype()) + '\t' +
            str(fobj.getlegal())[2:-2] + '\t' +
            str(fobj.getgrantor())[2:-2] + '\t' +
            str(fobj.getgrantee())[2:-2] + '\t' +
            str(fobj.getnotes()) + '\n')


def main():
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
              9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    daysinmonth = {'January': 31, 'February': 28, 'March': 31, 'April': 30,
                   'May': 31, 'June': 30, 'July': 31, 'August': 31, 'September': 30,
                   'October': 31, 'November': 30, 'December': 30}

    outputfiles =   {
                    31: 'Burt',
                    25: 'Butler',
                    43: 'Colfax',
                    24: 'Cuming',
                    28: 'Hamilton',
                    7: 'Madison',
                    46: 'Merrick',
                    10: 'Platte',
                    22: 'Saline',
                    6: 'Saunders',
                    16: 'Seward',
                    53: 'Stanton',
                    29: 'Washington',
                    27: 'Wayne'
                    }

    begdate, enddate = getDateRange()
    driver = webdriver.Chrome()

    createfiles(outputfiles)

    for county in outputfiles.keys():
        lookup = 'http://www.nebraskadeedsonline.us/search.aspx?county=' + str(county)
        outputfile = 'RAW ' + outputfiles[county] + '.txt'
        mydate = enddate
        getData(driver, outputfile, county, lookup,
                months[begdate.month], str(begdate.day), str(begdate.year),
                months[enddate.month], str(enddate.day), str(enddate.year))

        #while mydate >= begdate:
            #if mydate.weekday() < 5:
                #getData(driver, outputfile, county, lookup, months[mydate.month], str(mydate.day), str(mydate.year))
            #mydate = mydate - timedelta(days=1)

    driver.close()

    combinefiles(outputfiles)

main()
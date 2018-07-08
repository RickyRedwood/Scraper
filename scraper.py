from selenium import webdriver
from selenium.webdriver.support.ui import Select
import requests
from bs4 import BeautifulSoup
from datetime import date
from datetime import timedelta


def calcnumpages(numrecs):
    numpages = numrecs // 20
    if numrecs % 20 == 0:
        numpages = numpages - 1
    return numpages + 1


def getData(driver, f, county, lookup, m, d, y):
    driver.get(lookup)
    driver.find_element_by_link_text("Advanced Options").click()
    driver.find_element_by_id("cmbMonth1").click()
    Select(driver.find_element_by_id("cmbMonth1")).select_by_visible_text(m)
    driver.find_element_by_id("cmbMonth1").click()
    driver.find_element_by_id("cmbDay1").click()
    Select(driver.find_element_by_id("cmbDay1")).select_by_visible_text(d)
    driver.find_element_by_id("cmbDay1").click()
    driver.find_element_by_id("cmbYear1").click()
    Select(driver.find_element_by_id("cmbYear1")).select_by_visible_text(y)
    driver.find_element_by_id("cmbYear1").click()
    driver.find_element_by_id("cmbMonth2").click()
    Select(driver.find_element_by_id("cmbMonth2")).select_by_visible_text(m)
    driver.find_element_by_id("cmbMonth2").click()
    driver.find_element_by_id("cmbDay2").click()
    Select(driver.find_element_by_id("cmbDay2")).select_by_visible_text(d)
    driver.find_element_by_id("cmbDay2").click()
    driver.find_element_by_id("cmbYear2").click()
    Select(driver.find_element_by_id("cmbYear2")).select_by_visible_text(y)
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
            print('looking for link =', str(x))
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

    with open(f, 'w') as outfile:
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
                    print(row)
                    outfile.write(str(row) + '\n')


def main():
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
              9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    daysinmonth = {'January': 31, 'February': 28, 'March': 31, 'April': 30,
                   'May': 31, 'June': 30, 'July': 31, 'August': 31, 'September': 30,
                   'October': 31, 'November': 30, 'December': 30}

    outputfiles =   {
                    #31: 'Burt',
                    #25: 'Butler',
                    #43: 'Colfax',
                    #24: 'Cuming',
                    #28: 'Hamilton',
                    7: 'Madison',
                    #46: 'Merrick',
                    #10: 'Platte',
                    #22: 'Saline',
                    #6: 'Saunders',
                    #16: 'Seward',
                    #53: 'Stanton',
                    #29: 'Washington',
                    #27: 'Wayne'
                    }

    begdate, enddate = getDateRange()
    driver = webdriver.Chrome()

    for county in outputfiles.keys():
        lookup = 'http://www.nebraskadeedsonline.us/search.aspx?county=' + str(county)
        outputfile = 'RAW ' + outputfiles[county] + '.txt'
        with open(outputfile, 'w') as f:
            mydate = enddate
            while mydate >= begdate:
                if mydate.weekday() < 5:
                    getData(driver, outputfile, county, lookup, months[mydate.month], str(mydate.day), str(mydate.year))
                mydate = mydate - timedelta(days=1)

    driver.close()

main()
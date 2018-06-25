import datetime
import re
import sys
from datetime import date
from shutil import copy2

import requests
from bs4 import BeautifulSoup
from nameparser import HumanName


# This program will read a data file of urls to scrape the html from the page.
# Next, it will parse the data into a format that is suitable for export.
# After that, it will attempt to parse the name data in the file.
# Finally, it will capture any exceptions so they can be processed separately.


def datasplitter(lineno=1):
    """
    This function will take the standardized datafile and split each line into a list.
    This will let the program manipulate the data in an efficient manner. Output will go the proper data files
    for import into Excel.
    """
    with open(datafilename, 'r') as datafile, open(deedfilename, 'w') as deedfile, \
            open(releasefilename, 'w') as releasefile, open(exceptionfilename, 'w') as exceptionfile:
        if debugging == 'Y':
            for x in range(0, linestoskip - 1):
                dataline = datafile.readline()
            lineno = linestoskip
        dataline = datafile.readline()

        firsttime = True
        while dataline != '':
            datalist = dataline.split("\'")[1::2]  # splits the dataline into a properlist
            try:
                county = datalist[0]
                infodate = datalist[1]
                legal = datalist[2]
                grantor = datalist[3]
                grantee = datalist[4]
                deedtype = datalist[5]
                notes = ''
                datalist.append(notes)
            except IndexError:
                exceptionfile.write(dataline)

            if len(datalist) == 7:
                # county has been defined in the try statement
                # fix infodate
                if getnewlinecount(infodate) == 1:
                    index = infodate.find(tilde)
                    instrument = infodate[:index]
                    date = infodate[index + 1:]
                else:
                    index = infodate.find(tilde)
                    instrument = infodate[:index]
                    newindex = infodate.find(tilde, index + 1)
                    date = infodate[index + 1:newindex]
                    notes = notes + '(' + infodate[newindex + 1:] + ')'

                # get the deed type here
                deedtuple = fixdeed(deedtype, county)
                deedtype = deedtuple[0]
                notes = notes + deedtuple[1]

                # now we need to fix legal here
                legal = fixlegal(legal, deedtype)

            if firsttime:
                dots = 0
                print('Writing output files')
                firsttime = False
            else:
                dots = dots + 1
                sys.stdout.write('.')
                sys.stdout.flush()
                if dots % 80 == 0:
                    print('')

            if debugging == 'Y':
                # put whatever output you want for debugging here
                print('line =', lineno)
                print('grantor =', parsename(grantor, deedtype, True, county))
                print('grantee =',parsename(grantee, deedtype, False, county))
                print('date =', date)
                print('-'*80)
                print()
            else:
                if deedtype == 'Warranty' or deedtype == 'Quitclaim' or deedtype == 'Trustee' or deedtype == 'Pers Rep' or \
                        deedtype == 'DOT':
                    deedfile.write('"' + county + '",' + '"' + deedtype + '",' + '"' + fixlegal(legal, deedtype) + '",'
                                   + '"' + parsename(grantor, deedtype, True, county) + '",' + '"' +
                                   parsename(grantee, deedtype, False, county) + '",' + '"' + notes + '"' + '\n')
                elif deedtype == 'DOR' or deedtype == 'Misc' or deedtype == 'NOD' or deedtype == 'Cancel NOD' or \
                        deedtype == 'Fed Lien' or deedtype == 'Fed Rel':
                    releasefile.write('"' + county + '",' + '"' + deedtype + '",' + '"' + fixlegal(legal, deedtype) + '",'
                                      + '"' + parsename(grantor, deedtype, True, county) + '",' + '"'
                                      + parsename(grantee, deedtype, False, county) + '",' + '"' + notes + '"' + '\n')
                elif deedtype == 'State Lien' or deedtype == 'State Rel':
                    releasefile.write('"' + county + '",' + '"' + deedtype + '",' + '"' + fixlegal(legal, deedtype) + '",'
                                      + '"' + 'Dept of Revenue' + '",' + '"'
                                      + parsename(grantor, deedtype, True, county) + '",' + '"' + notes + '"' + '\n')
                elif deedtype == 'Exception':
                    pass
                else:
                    exceptionfile.write('"' + infodate + '",' + '"' + county + '",' + '"' + deedtype + '",' + '"' + legal + '",'
                                        + '"' + grantor + '",' + '"' + grantee + '",' + '"' + notes + '"' + '\n')
            dataline = datafile.readline()
            lineno = lineno + 1


def fixdeed(deed, legalcounty):
    billofsale = ('BOS',)
    cancelnod = ('CANCEL', 'CANDEF', 'CANNOD', 'CND', 'CNOD', 'CNTDF', 'PCND', 'RNOD',)
    clrelease = ('CLR', 'RCL', 'RELCL',)
    conditionaluse = ('CONUSE',)
    conservator = ('CONSD',)
    constlien = ('CL', 'C LIEN', 'CLIEN',)
    easements = ('EADN/C', 'EAS', 'EASA', 'EASAS', 'EASAGT', 'EASE', 'EASED', 'EASMT', 'ESMT',
                 'EASN/C', 'EASENC', 'ESMDEE', 'PEREAS',)
    exceptions = ("'1'", "'2'", '1', '2', '4', '~~12~~',
                  'AAA', 'AACT',
                  'ACK', 'ACKM', 'ACOV', 'ACPOA', 'ACVPOA',
                  'ADDEND', 'ADMPLA', 'ADOM',
                  'AEAS',
                  'AFD', 'AF/DD', 'AFDEED', 'AFDMTG',
                  'AFF', 'AFFAFF', 'AFFDC', 'AFF&DC', 'AFFDM', 'AFFDTH', 'AFFIX', 'AFFI',
                  'AFFID', 'AFFMH', 'AFFMIS', 'AFFMS', 'AFFMTG', 'AFFNOP', 'AFFPOS', 'AFFSCR', 'AFFSUC',
                  'AFF/TR', 'AFFTRA', 'AFFX', 'AFT',
                  'AGMT', 'AGMMTG', 'AGMTPL', 'AGR', 'AGR/MT', 'AGRMTG', 'AGRPLN', 'AGRPRL', 'AGTCRT',
                  'ALL', 'ALOR', 'ALSE',
                  'AMAGR', 'AMDOT', 'AMEASE', 'AMEMLE', 'AMEND', 'AMFS', 'AMRC', 'AMSA',
                  'AOC', 'AOR', 'AORD', 'AOST', 'AOV',
                  'APCU', 'APL', 'APP TR', 'APPMTG', 'APPST', 'APPT',
                  'ARENTS', 'ART',
                  'ASDOT', 'ASFF', 'ASGN', 'ASGTRT', 'ASL&R', 'ASLERT', 'ASMTG', 'ASMTLE', 'ASRENT', 'ASSEA', 'ASSGT',
                  'ASSI', 'ASSI/E', 'ASSIGN',
                  'ASSLSE', 'ASSN', 'ASSNLR', 'ASSR', 'ASSRNT', 'ASTR', 'ASSSUM',
                  'ATD', 'ATREDC', 'ATWOP',
                  'BCD', 'BCP', 'BOND',
                  'C DEED', 'C DOD',
                  'CA', 'CASSI',
                  'CCQCD',
                  'CD', 'CDC', 'CDEED', 'CDOR', 'CDOT',
                  'CEMD',
                  'CERDIS', 'CERMTG', 'CERT', 'CERTAM', 'CERTCT', 'CERTDC', 'CERTIF', 'CERTTR', 'CERTUS',
                  'CERWIL',
                  'CNOC', 'CNT',
                  'CODOR', 'COJTWD', 'CONTSA', 'CODEED', 'COLN', 'COMDOT', 'CON', 'CONSLT', 'CONTFF', 'CONTRA', 'CONTRD',
                  'CORAFA', 'CORAFF', 'CORASG', 'CORD', 'CORDC', 'CORPRD', 'CORPRE', 'CORRAS', 'CORRD',
                  'CORRQD', 'CORPWD', 'CORRWD',
                  'CORTRD', 'CORTRU', 'CORWD', 'COT', 'COTTD', 'COV', 'COVE', 'COVEN', 'COWD',
                  'CP', 'CPA', 'CPLAT', 'CPOA', 'CPR D', 'CPRD', 'CPREPD',
                  'CQCD',
                  'CRWD',
                  'CSOT', 'CSUBA',
                  'CTA', 'CTDAOR',
                  'DBYTR',
                  'DC', 'DCERTD', 'DCTODD',
                  'DEATH', 'DECLAR', 'DEDE', 'DEDI', 'DEDICA', 'DEM',
                  'DISHST',
                  'DOH',
                  'DPART',
                  'DRESCO',
                  'DSCH',
                  'ED', 'ESCNAG', 'EXNOCM',
                  'FF', 'FFC', 'FFT',
                  'FINSTM', 'FIX', 'FIXQCD',
                  'FQCD',
                  'FROR',
                  'FS', 'FSAMDT', 'FSAMEN', 'FSC', 'FSCONT', 'FSPREL', 'FST', 'FSTERM',
                  'HOME',
                  'LEASE',
                  'LIC', 'LICS',
                  'LMA', 'LMOD',
                  'LOTBCH', 'LOTSPL',
                  'LSA', 'LSE', 'LSO', 'LS&PL', 'LSPL', 'LSUB',
                  'LTCON', 'LTDSUB', 'LTSP',
                  'MACO', 'MCONR',
                  'MHAFF',
                  'MOA',
                  'NAO',
                  'NCN', 'NCOM',
                  'NOAL', 'NOAMDE',
                  'NOC', 'NCOM', 'NOE', 'NOS', 'NOT', 'NOTCOM', 'NOTEXT', 'NOTMTG', 'NOTICE', 'NOTN/C', 'NOTS',
                  'NOTTRS',
                  'NRFR',
                  'NTC', 'NTCCOM', 'NTCMTG', 'NTRSL',
                  'OPT', 'OPTION',
                  'ORD', 'ORDS',
                  'PA', 'PARWAL', 'PARTD', 'PARWD', 'PAT',
                  'PCON',
                  'PLAT',
                  'PRAOR', 'PROCOV', 'PRPUB',
                  'PSA',
                  'PTRALR', 'PTREAL', 'PTTRUS',
                  'PURAGR', 'PUROP',
                  'RAOR', 'RCNL',
                  'RDOR',
                  'REAGRM', 'REAPP',
                  'REDEV', 'REDOT',
                  'REF',
                  'RELASN', 'RELASM', 'RELSRT', 'RELASR', 'REL-D', 'RELEAS', 'RELREC', 'RELSEV',
                  'RENO', 'RENUN',
                  'REPLAT',
                  'REQ', 'REQNOT', 'REQUE', 'REQUES', 'RES',
                  'REQCPY', 'REQREC',
                  'RERA', 'RESCIN', 'RESCOV',  'RESNF', 'RESOL', 'RESTCV',
                  'RETAGM', 'RETAGR', 'REVTOD',
                  'RFN', 'RFNOD', 'RFR', 'RFTL',
                  'RIFIRE',
                  'RLCPA', 'RLSAOR', 'RLSASS', 'RLSMSC', 'RLSCON', 'RLSSA',
                  'RNDND', 'RNDNS', 'RNOT',
                  'ROR',
                  'RQRCVY',
                  'RRFR',
                  'RSA',
                  'RTODD',
                  'SA',
                  'SB MTG', 'SBA', 'SBAG', 'SBSR', 'SBT TR', 'SBTR', 'SBTRCE',
                  'SCORWD', 'SCRAFF', 'SDOT',
                  'SEC', 'SECAGR', 'SEV', 'SEVAGT', 'SEVCA',
                  'SID',
                  'SMTG',
                  'SOL', 'SOT',
                  'SP',
                  'STCONT', 'STMTAU', 'STXCON',
                  'SUB', 'SUBA', 'SUBAGM', 'SUBAGR', 'SUBAGT', 'SUBD', 'SUBDOR', 'SUBMTG', 'SUBO', 'SUBOMO', 'SUBORD',
                  'SUBTR', 'SUBTRU', 'SUR', 'SURN/C', 'SURREP', 'SURVEY',
                  'SWDC',
                  'TCIAC',
                  'TDM',
                  'TER', 'TERETC', 'TERM', 'TERMEA', 'TERMML', 'TERMTG', 'TERSA',
                  'TFIX', 'TLEASE', 'TLSE', 'TERLSE',
                  'TNOC',
                  'TODD',
                  'TPDR',
                  'TRAFF', 'TRDART',
                  'UAMD',
                  'UCCA', 'UCCC', 'UCCTER', 'UCC', 'UCCT', 'UCNT', 'UCT',
                  'UEVS',
                  'UFS', 'UTER',
                  'VOID',
                  'WAI', 'W/SLN', 'WAIVE', 'WAIVTD', 'WAVFR', 'WOD', 'WVR',
                  'ZONE',)
    fedliens = ('FED', 'FEDTAX', 'FTXL')
    fedreleases = ('FEDREL', 'FEDRLS', 'FEDTER', 'FTR', 'FTXREL',)
    lien = ('LIEN', 'UTLN',)
    lienrelease = ('LIENR', 'RELLN', 'RLSLN',)
    lispendens = ('LIS', 'LISPEN', 'NLP',)
    lispendensrelease = ('LISPRL', 'RLP',)
    mastercommisioner = ('MASTD', 'MCD',)
    mechlien = ('MECH', 'MLIEN',)
    memos = ('MEMAGM', 'MEMLEA', 'MEMLSE', 'MEM', 'MEMO', 'MEMOPT', 'MEMRED', 'MEMTRA', 'MHOEC', 'MOL',)
    modifications = ('ADDDOT', 'DOTMOD',
                     'MDOT', 'MOD', 'MOD DT', 'MODA', 'MODAGM', 'MODAGR', 'MODDOT', 'MODIFI', 'MODMTG', 'MODTRT',
                     'TDMOD', 'TRDMOD',)
    mortgages = ('CMDOT', 'CONDOT',
                 'D T', 'DISTD', 'DDOT', 'DISDOT', 'DISMTG', 'DOT', 'DOT2', 'DOTAR', 'DOT/AR', 'DOTASN',
                 'DOTASR', 'DOTASS', 'DOTAST', 'DOT/SA',
                 'MOR', 'MTG', 'MTGE', 'NOTE',
                 'SDDOT', 'SECDOT', 'SUBDOT',
                 'TD&AR', 'TRDAOR', 'TRDEED', 'TTAS',
                 'WAVDOT', 'WAIMTG',)
    miscnotes = ''
    nodlist = ('MECHLN', 'NOD', 'NTCDFT', 'NOTDEF',)
    partials = ('DOPR', 'PDOR', 'PR', 'PTDREC', 'PT REC', 'PT REL', 'PTMR', 'PTRECO', 'PTREL', 'STPREL',)
    persreps = ('D OF D', 'DDIS', 'DDIST', 'DDCPR', 'DISTB', 'DDPR', 'DOD', 'JTPRD',
                'PRD', 'PRDEED', 'PRJTD', 'PRJTWD',)
    poas = ('AFPOA', 'DPOA', 'LTDPOA', 'POA', 'POAM',)
    propliens = ('PL',)
    quitclaims = ('JTQC', 'JTQCD', 'QCD',)
    releases = ('DOR',
                'FREC', 'FRECON', 'FULLRC',
                'MR',
                'RECON', 'RECVY', 'REL', 'RELMTG', 'RLS', 'RLEASE', 'RLS-MG',
                'SAT', 'SATIS', 'SBTRDR', 'SDOR', 'SOTDOR', 'SOTREC', 'ST&DR', 'SUB/RE', 'SUTRDR', 'SUBTRDR',
                'TDOR', 'TR D R', 'TRSREC', 'TRUSRE',)
    sheriffdeed = ('SD', 'SHERD',)
    stateliens = ('STL', 'STTAX', 'STXL',)
    statereleases = ('STT', 'STTERM', 'STXT', 'STXTER',)
    taxdeeds = ('TREATD',)
    tempeasement = ('TEMEAS',)
    trusteedeeds = ('DINTR', 'DIT',
                    'SCTD',  # Successor Co-Trustees Deed in Hamilton County
                    'TD', 'TDOD', 'TJTD', 'TRASST', 'TRD', 'TREED',
                    'TRS D', 'TRSD', 'TRSJTD', 'TRSWD', 'TRTD', 'TRUSTD', 'TSD', 'TWD', 'TRWTY',)
    warrantydeeds = ('CJTWD', 'CORPD', 'CORPWD', 'CWD',
                     'DEED',
                     'JTD', 'JTDPOA', 'JTWD',
                     'LLCJTD', 'LLCWD',
                     'PARTWD', 'PRTWD', 'PTNRWD', 'PWD',
                     'SPWD', 'SPWTY', 'SRVWTY', 'SWD',
                     'WD', 'WTY',)

    if deed in warrantydeeds:
        deedtype = 'Warranty'
    elif deed in conservator:
        deedtype = 'Warranty'
        miscnotes = "(Conservator's Deed) "
    elif deed in taxdeeds:
        deedtype = 'Warranty'
        miscnotes = "(Treasurer's Tax Deed) "
    elif deed in sheriffdeed:
        deedtype = 'Warranty'
        miscnotes = miscnotes + "(Sheriff's Deed) "
    elif deed in mastercommisioner:
        deedtype = 'Warranty'
        miscnotes = miscnotes + "(Master Commissioner's Deed) "
    elif deed in quitclaims:
        deedtype = 'Quitclaim'
    elif deed in persreps:
        deedtype = 'Pers Rep'
    elif deed in trusteedeeds:
        deedtype = 'Trustee'
    elif deed in mortgages:
        deedtype = 'DOT'
        isdeed = True
    elif deed in modifications:
        deedtype = 'DOT'
        miscnotes = miscnotes + '(Modification) '
    elif deed in releases:
        deedtype = 'DOR'
    elif deed in partials:
        deedtype = 'DOR'
        miscnotes = miscnotes + '(Partial) '
    elif deed in nodlist:
        deedtype = 'NOD'
    elif deed in constlien:
        deedtype = 'NOD'
        miscnotes = miscnotes + '(Construction Lien) '
    elif deed in mechlien:
        deedtype = 'NOD'
        miscnotes = miscnotes + "(Mechanic's Lien )"
    elif deed in lispendens:
        deedtype = 'NOD'
        miscnotes = miscnotes + '(Notice of Lis Pendens) '
    elif deed in lispendensrelease:
        deedtype = 'Cancel NOD'
        miscnotes = miscnotes + '(Release of Lis Pendens) '
    elif deed in cancelnod:
        deedtype = 'Cancel NOD'
        if deed == 'PCND':
            miscnotes = miscnotes + '(Partial Cancellation of Notice of Default) '
    elif deed in clrelease:
        deedtype = 'Cancel NOD'
        miscnotes = miscnotes + '(Construction Lien Release) '
    elif deed in lienrelease:
        deedtype = 'Cancel NOD'
        miscnotes = miscnotes + '(Lien Release) '
    elif deed in billofsale:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Bill of Sale) '
    elif deed in easements:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Easement) '
    elif deed in conditionaluse:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Conditional Use Permit) '
    elif deed in lien:
        deedtype = 'NOD'
        miscnotes = miscnotes + '(Lien) '
    elif deed in fedliens:
        deedtype = 'Fed Lien'
    elif deed in fedreleases:
        deedtype = 'Fed Rel'
    elif deed in memos:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Memo) '
    elif deed in poas:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Power of Attorney) '
    elif deed in propliens:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Property Lien) '
    elif deed in stateliens:
        deedtype = 'State Lien'
    elif deed in statereleases:
        deedtype = 'State Rel'
    elif deed in tempeasement:
        deedtype = 'Misc'
        miscnotes = miscnotes + '(Temporary Easement) '
    elif deed in exceptions:
        deedtype = 'Exception'
    else:
        deedtype = deed

    # catch the counties that use a different abbreviation than above
    if legalcounty == 'Merrick' and deed == 'TD':
        deedtype = 'DOT'
    if legalcounty == 'Burt' and deed == 'TD':
        deedtype = 'DOT'
    if legalcounty == 'Platte' and deed == 'TD':
        deedtype = 'DOT'
    if legalcounty == 'Hamilton' and deed == 'TD':
        deedtype = 'DOT'
    if legalcounty == 'Wayne' and deed == 'TRTD':
        deedtype = 'Trustee'
    if legalcounty == 'Butler' and deed == 'CONDOT':
        deedtype = 'NOD'
        miscnotes = miscnotes + '(Construction Lien) '

    return deedtype, miscnotes


def fixint():
    """
    this fixes the intermediate file in order to make it standardized and outputs it to datafile.txt
    """
    counties = ('Burt', 'Butler',
                'Colfax', 'Cuming',
                'Hamilton',
                'Madison', 'Merrick',
                'Platte',
                'Saline', 'Saunders', 'Seward', 'Stanton',
                'Washington', 'Wayne')
    newline = '\n'

    with open(intfilename, 'r') as intfile, open(datafilename, 'w') as datafile:
        dataline = intfile.readline()
        iscounty = False
        mylist = []
        linesread = 1
        field = ''
        firsttime = True
        while dataline != '':
            if dataline[:-1] in counties:
                iscounty = True
                county = dataline[:-1]
            if not iscounty:
                startindex = 0
                endindex = -1
                while (startindex != -1 or endindex != -1):
                    startindex = dataline.find("\'", endindex + 1)
                    if startindex != -1:  # we found something!
                        endindex = dataline.find("\'", startindex + 1)
                        if startindex != -1 and endindex != -1:
                            field = dataline[startindex:endindex + 1]
                            # now we play with field
                            field = field.replace(newline, '~')
                            mylist.append(field)
                    else:
                        endindex = -1
                mylist.insert(0, county)
                datafile.write(str(mylist) + '\n')
            mylist = []
            iscounty = False
            dataline = intfile.readline()
            if firsttime and debugging != 'Y':
                print('')
                dots = 0
                print('Reading intermediate file')
                firsttime = False
            else:
                if debugging != 'Y':
                    dots = dots + 1
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    if dots % 80 == 0:
                        print('')
    print('copying...')
    copy2(datafilename, 'input.txt')
    print('file copied')

    with open('input.txt', 'r') as inputfile, open(datafilename, 'w') as datafile:
        dataline = inputfile.readline()
        while dataline != '':
            dataline = dataline.replace('\"', '')
            dataline = dataline.replace('\\n', '~')
            dataline = dataline.replace('\\~', '~')
            dataline = dataline.replace('[', '')
            dataline = dataline.replace(']', '')
            dataline = re.sub(r'-?\bPR~', r' PERS REP~', dataline)
            dataline = re.sub(r',?[^A-Z]N\.?A\.?[^A-Z]', r'', dataline)
            dataline = dataline.replace('DECD', 'ESTATE')
            dataline = dataline.replace(', FLCA', '')
            dataline = dataline.replace('FLCA', '')
            dataline = dataline.replace('A/K/A', 'AKA')
            dataline = dataline.replace('F/K/A', 'FKA')
            dataline = dataline.replace('N/K/A', 'NKA')
            dataline = dataline.replace('D/B/A', 'DBA')
            dataline = dataline.replace('F/D/B/A', 'FDBA')
            dataline = re.sub(r"(?<!TO )THE PUBLIC", "TO THE PUBLIC", dataline)
            dataline = re.sub(r' BY~', r' BY ', dataline)
            datafile.write(dataline)
            dataline = inputfile.readline()


def fixlegal(desc, deed):
    """ Fixes the legal description scraped from an HTML page """
    counties = ('Burt', 'Butler', 'Cuming', 'Colfax', 'Hamilton', 'Madison', 'Merrick',
                'Platte', 'Saline', 'Seward', 'Stanton', 'Washington', 'Wayne')
    funclegal = desc
    funclegal = funclegal.title()
    # get rid of any double spaces
    funclegal = ' '.join(funclegal.split())

    # fix the fractionals
    # these are the half sections
    # 00BD is the unicode representation for 1/2
    funclegal = re.sub(r"\b([NEWSnews]) ?(1/)?2", regupper, funclegal)
    funclegal = funclegal.replace('N 1/2', 'N\u00BD')
    funclegal = funclegal.replace('E 1/2', 'E\u00BD')
    funclegal = funclegal.replace('W 1/2', 'W\u00BD')
    funclegal = funclegal.replace('S 1/2', 'S\u00BD')

    # now the quarter sections
    # 00BC is the unicode representation for 1/4
    funclegal = re.sub(r'([NSns][EWew]) ?(1/)?4', regupper, funclegal)
    funclegal = funclegal.replace('NE 1/4', 'NE\u00BC')
    funclegal = funclegal.replace('NW 1/4', 'NW\u00BC')
    funclegal = funclegal.replace('SE 1/4', 'SE\u00BC')
    funclegal = funclegal.replace('SW 1/4', 'SW\u00BC')
    funclegal = funclegal.replace('NE1/4', 'NE\u00BC')
    funclegal = funclegal.replace('NW1/4', 'NW\u00BC')
    funclegal = funclegal.replace('SE1/4', 'SE\u00BC')
    funclegal = funclegal.replace('SW1/4', 'SW\u00BC')

    # 00BE is the unicode representation for 3/4
    funclegal = re.sub(r"([NSns][EWew]) ?3/4", regupper, funclegal)
    funclegal = funclegal.replace('NE 3/4', 'NE\u00BE')
    funclegal = funclegal.replace('NW 3/4', 'NW\u00BE')
    funclegal = funclegal.replace('SE 3/4', 'SE\u00BE')
    funclegal = funclegal.replace('SW 3/4', 'SW\u00BE')

    # fix non-breaking spaces
    funclegal = funclegal.replace(r'\\xao', '')

    # fix ordinal numbers
    funclegal = funclegal.replace('1St ', '1st ')
    funclegal = funclegal.replace('2Nd ', '2nd ')
    funclegal = funclegal.replace('3Rd ', '3rd ')
    for x in range(4, 20):
        funclegal = funclegal.replace(str(x) + 'Th ', str(x) + 'th ')

    # clean up the text
    # unusual subd names
    funclegal = re.sub(r'\bMc([a-z]*)\b', regtitle, funclegal)
    funclegal = re.sub(r'Cmh', r'CMH', funclegal)

    # find Roman numbers
    funclegal = re.sub(r'\b(Xc|Xl|L?[X|x]{0,3})*([I|i]x|[I|i]v|[V|v]?[I|i]{0,3})\b', regupper, funclegal)

    # looking for whole words using regex
    funclegal = funclegal.replace('  ', ' ')
    funclegal = re.sub(r'\bA\b', r'a', funclegal)
    if funclegal.startswith('a'):
        funclegal = funclegal.replace('a', 'A', 1)
    funclegal = re.sub(r'Block(s?) a', r'Block\1 A', funclegal) # need to fix Block a to show up as Block A
    funclegal = re.sub(r'Outlot(s?) a', r'Outlot\1 A', funclegal)
    funclegal = re.sub(r'Unit(s?) a', r'Unit\1 A', funclegal)
    funclegal = re.sub(r'\bAddition\b', r'Add', funclegal)
    funclegal = re.sub(r'\bAddn\b', r'Add', funclegal)
    funclegal = re.sub(r'\bAn\b', r'an', funclegal)
    funclegal = re.sub(r'\bAnd\b', r'and', funclegal)
    funclegal = re.sub(r'\bAt\b', r'at', funclegal)
    funclegal = re.sub(r'\bIn\b', r'in', funclegal)
    funclegal = re.sub(r'\bOf\b', r'of', funclegal)
    funclegal = re.sub(r'(\d), of', r'\1 of', funclegal)
    funclegal = funclegal.replace('of of', 'of')
    funclegal = funclegal.replace('of.', 'of')
    funclegal = re.sub(r'\bPt\b', r'Part of', funclegal)
    funclegal = funclegal.replace('(Pt)', '(pt)')
    funclegal = re.sub(r'\bRr\b', regupper, funclegal)
    funclegal = re.sub(r'\bSd\b', r'Subd', funclegal)
    funclegal = re.sub(r'\bSubdivision\b', r'Subd', funclegal)
    funclegal = re.sub(r'\bThe\b', r'the', funclegal)
    funclegal = re.sub(r'\bTo\b', r'to', funclegal)
    funclegal = re.sub(r'\bWith\b', r'with', funclegal)

    # get rid of Orig Town of Town messages
    funclegal = re.sub(r'([A-Z][a-z]+) of \1', r'of \1', funclegal)
    funclegal = re.sub(r'([A-Z][a-z]+ ([A-Z][a-z]+)) of \1', r'of \1', funclegal)


    # get rid of the See Exception messages
    funclegal = re.sub(r'\({0,1}See Exceptions{0,1}(\)|~){0,1}', r'', funclegal)
    funclegal = re.sub(r'\({0,1}For Exceptions{0,1}(\)|~){0,1}', r'', funclegal)

    # get rid of the See Legal messages
    funclegal = re.sub(r'\({0,1} ?See Legal(\)|~){0,1}', r'', funclegal)

    # get rid of See Easement messages
    funclegal = re.sub(r'(?:and|And){0,1} ?((s|S)ee)? ?((e|E)asement)', r'', funclegal)

    # get rid of non-breaking spaces and other punctuation
    funclegal = funclegal.replace(r'\\Xa', '')
    funclegal = funclegal.replace(';,', ';')
    funclegal = re.sub(r'(\d,)(\d)', r'\1 \2', funclegal)
    funclegal = re.sub(r'\*[s|S]', r's', funclegal)

    # see if there is extra info in record
    if funclegal.find('...') != -1:
        funclegal = funclegal.replace('...', '(Legal description length exceeds field size)')

    # clean up county names
    funclegal = funclegal.replace('County, Nebraska', 'County Nebraska')
    for countyname in counties:
        funclegal = funclegal.replace(countyname + ' County Nebraska', '')

    # clean up State and Federal Liens and releases
    if deed == 'State Rel' or deed == 'Fed Rel' or deed == 'State Lien' or deed == 'Fed Lien':
        funclegal = ''

    # fix EOL issues
    if funclegal.endswith(',;~'):
        funclegal = funclegal[:-3]
    if funclegal.endswith(',;'):
        funclegal = funclegal[:-2]
    if funclegal.endswith(', ~'):
        funclegal = funclegal[:-3]
    if funclegal.endswith('~'):
        funclegal = funclegal[:-1]
    funclegal = funclegal.replace('~', '; ')
    funclegal = funclegal.replace(', ;', '; ')
    if funclegal.endswith(','):
        funclegal = funclegal[:-1]

    return funclegal


def getdefaultdate():
    today = date.today()
    if today.weekday() <= 3:
        days2add = 4 - today.weekday()
    else:
        days2add = 11 - today.weekday()
    today = today + datetime.timedelta(days=days2add)
    if today.month < 10:
        mymonth = '0' + str(today.month)
    else:
        mymonth = str(today.month)
    if today.day < 10:
        myday = '0' + str(today.day)
    else:
        myday = str(today.day)
    myyear = str(today.year)[-2:]
    mydate = mymonth + myday + myyear
    return mydate


def getnewlinecount(mystr):
    count = str(mystr).count(tilde)
    return count


def parsename(name, deedtype, isgrantor, county):
    ''' This function parses the name of the grantor/grantee that is passed to it. '''
# The parameters are name (a list), deedtype (a string), and isgrantor (boolean).

# This section is going to check how many names are in the item that was passed to this function
    parselist = []
    goodparse = []
    beg = 0
    parselist = name.split('~')
    parselist = [x.replace(',  ', ', ') for x in parselist]
    if deedtype == 'State Rel' or deedtype == 'State Lien':
        if county != 'Burt':
            parselist = [re.sub(r'(?:NEBR(?:ASKA)? ?|STATE ?)?(?:DEP(?:ARTMEN)?T) OF REV(?:ENUE)?',
                         r'DEPT OF REVENUE', x) for x in parselist]
        else:
            parselist = [re.sub(r'(?:NEBR(?:ASKA)? ?|STATE ?)?(?:DEP(?:ARTMEN)?T) OF REV(?:ENUE)?',
                                r'', x) for x in parselist]
    del parselist[-1]  # split adds a blank element to the end of the list. don't know why. this gets rid of it
    parsedname = ''
    for parseme in parselist:
        myval = whoami(parseme)

        if myval == 0:  # human
            parseme = re.sub(r' ?-? ?(AS )?INDIVIDUAL(LY)?', r'', parseme)  # removes individual(ly) from name
            parseme = re.sub(r' ?-? ?HUSB(AND) ?(JT)? ?(WROS)?', r'', parseme)  # removes husband from name
            parseme = re.sub(r' ?-? ?WIFE ?(JT)? ?(WROS)?', r'', parseme)  # removes wife from name
            parseme = re.sub(r' ?-? ?JOINT TENANTS', r'', parseme)  # removes joint tenants from name
            if re.search(r'DATED(.*)', parseme) is not None:
                parseme = ''
                continue
            if parseme.count(',') >= 2:
                # we've got something weird like SMITH, KEVIN, JAMES
                parseme = re.sub(',', ' ', parseme)  # get rid of commas
                parseme = re.sub('  ', ' ', parseme)
                parseme = parseme.replace(' ', ', ', 1)  # replace the first occurrence of a space with a comma
            if county == 'Madison' or county == 'Platte':
                # these counties don't place commas in their names even though they're last first middle
                parseme = parseme.replace(',', '')  # get rid of commas
                parseme = parseme.replace(' ', ', ', 1)  # replace the first occurrence of a space with a comma
            parsedname = HumanName(parseme)
            parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                        ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                        parsedname.nickname.title()
            parsedname = parseme  # need to assign parseme to parsedname so it will carry out of the for loop
            if parsedname.strip() == 'To The Public':
                parsedname = 'the Public'
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 1 or myval == 11 or myval == 257 or myval == 259:  # bank or bank & trustee so we make it a bank
            parsedname = parseme
            # cleaning up items that exist in bank names
            parseme = re.sub(r',? ?PCA', r'', parseme)
            parseme = re.sub(r',? ?N\.? ?A\.?\b', r'', parseme)
            parseme = re.sub(r' ?-?(\(SUCCESSOR)? ?(FOR)? ?(ESQ)? \(??TRUSTEE\)? ?\(?(ATTORNEY)?\)?', r'', parseme)
            parseme = re.sub(r'SUC TR', '', parseme)
            parseme = re.sub(r'(( ?- ?)?|(, )?)TRUSTEE\s', r'', parseme)
            parseme = re.sub(r',? ?,? ?TRUSTEE', r'', parseme)
            parseme = parseme.replace('F&M', 'F & M')
            parseme = re.sub(r',$', r'', parseme)
            # the following if statements look for something in the name that disqualifies the whole name
            # from being parsed
            if re.search(r'LOCHER (MR )?THOMAS ?(MR)?', parseme) is not None:
                parseme = ''
            if re.search(r'BENE\b|BENEFICIARY|BENEF\b', parseme) is not None:
                parseme = ''  # effectively getting rid of this name if it's listed as beneficiary in a bank
            if re.search(r'LENDER', parseme) is not None:
                parseme = ''  # removing name if it's listed as a lender
            if re.search(r'NOMINEE', parseme) is not None:
                parseme = ''  # removing name if it's listed as a lender
            if re.search(r'ASFOR', parseme) is not None or re.search(r'AS TRUSTEE FOR', parseme) is not None:
                parseme = ''  # removing name for being a trustee for someone else
            # putting title case together for banks that are working with loans and releases NOT transfers
            if (deedtype == 'DOT' and not isgrantor) or (deedtype == 'DOR' and isgrantor):
                parseme = parseme.title()
                parseme = parseme.replace('Bankfirst', 'BankFirst')
                parseme = parseme.replace('Loandepot.com', 'LoanDepot.com')
                parseme = parseme.replace('National Association', '')

            parsedname = parseme
            if len(parsedname) > 0:  # don't want to append it unless there is something there
                goodparse.append(parsedname)

        elif myval == 2 or myval == 3 or myval == 34 or myval == 258:  # business = 2, business & bank = 3 so we make it a business
            # real estate business = 34 so we make it a business
            # fortress credit co llc trustee = 258 so we make it a business
            parsedname = parseme
            parseme = parseme.replace(',', '')
            parseme = parseme.replace('.', '')
            parseme = re.sub(r'\b(INC).*', 'Inc', parseme)
            if re.search(r'NOMINEE', parseme) is not None:
                parseme = ''  # removing name if it's listed as a lender
            if re.search(r'CO-SUCCESSOR TRUSTEES OF THE', parseme):
                parseme = ''
            if re.search(r'CO( |-)TRUSTEE', parseme) is not None:
                myval == myval - 2
                continue
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 4:  # city
            parsedname = parseme
            parseme = re.sub(r',? ?\(?CITY OF\)? ?', '', parseme)
            parseme = re.sub(r',? ?NEBRASKA', '', parseme)
            parseme = 'CITY OF ' + parseme
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 8 or myval == 9 or myval == 10 or myval == 520:  # county
            parsedname = parseme
            parseme = parseme.replace('A NEBRASKA POLITICAL SUBDIVISION', '')
            parseme = re.sub(r'/b(.*) CO(?:UNTY)? ?(?:ATT)(?:ORNE)?Y(?:S)? OFFICE', r'\1 COUNTY ATTORNEY OFFICE', parseme)
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 16 or myval == 17 or myval == 272:  # credit union
            parsedname = parseme
            parseme = parseme.replace(', PCA', '')
            parseme = parseme.replace(', N.A.', '')
            parseme = parseme.replace(', NA', '')
            parseme = re.sub(r'(( ?- ?)?|(, )?)TRUSTEE\s', r'', parseme)
            parseme = re.sub(r'\bTRUSTEE', r'', parseme)
            parseme = re.sub(r'^(?:MERS)(?:/| )?(.*)', r'\1', parseme)
            parseme = re.sub(r',\s$', r'', parseme)
            #TODO: if there are other titles in the credit union name, i.e., Beneficiary, we need to remove those somewhere in here
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 32:  # estate
            if re.search(r'((CO ?)?-? ?P\.? ?R\.? ?)?OF THE ESTATE OF~', parseme) is not None:
                parseme = ''
                continue
            else:
                parseme = parseme.replace('P.R.', 'PERS REP')  # done first this fixes initials without a space after the period
                parseme = re.sub(r'(\w*)\.\b', r'\0 ', parseme)
                parseme = re.sub(r'((\w*), (\w*) (\w*)) \b(?<!REAL )ESTATE\b', r'\1', parseme)  # ex: LAST, FIRST MIDDLE ESTATE
                parseme = re.sub(r'((\w*), (\w*)\. (\w*)) \b(?<!REAL )ESTATE\b', r'\1', parseme)  # ex: LAST, FI. MIDDLE ESTATE
                parseme = re.sub(r'((\w*), (\w*) (\w*)\.) \b(?<!REAL )ESTATE\b', r'\1', parseme)  # ex: LAST, FIRST MI. ESTATE
                parseme = re.sub(r'ESTATE OF ((\w*) (\w*)? (\w*)?\b)', r'\1', parseme)  # ex: ESTATE OF FIRST M LAST (M is optional)
                parseme = re.sub(r'ESTATE', r'', parseme)
                parseme = re.sub(r'^ESTATE OF ', r'', parseme)
                if parseme.count(',') >= 2:
                    # we've got something weird like SMITH, KEVIN, JAMES
                    parseme = re.sub(',', ' ', parseme)  # get rid of commas
                    parseme = re.sub('  ', ' ', parseme)
                    parseme = parseme.replace(' ', ', ', 1)  # replace the first occurrence of a space with a comma
                parsedname = HumanName(parseme)
                parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                          ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                          parsedname.nickname.title() + ' ' + '(Estate)'
                parsedname = parseme
                if len(parsedname) > 0:
                    goodparse.append(parsedname)

        elif myval == 64 or myval == 320 or myval == 322:  # pers rep
            parseme = re.sub(r'\bCO-PR', r'',  parseme)
            parseme = re.sub(r'\bPR\b', r'', parseme)
            parseme = re.sub(r'-? *(?:CO)? ?-?PERS(?:ONAL)? ?REP(?:RESENTATIVE)?', r'', parseme)
            parsedname = HumanName(parseme)
            parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                        ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                        parsedname.nickname.title() + ' ' + '(Pers Rep)'
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 128 or myval == 130 or myval == 160:  # trust
            trusttitle = ''
            if myval != 130:
                if re.search(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)? LIVING TRUST', parseme):
                    searchObj = re.search(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)? LIVING TRUST', parseme)
                    parseme = re.sub(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)? LIVING TRUST', '', parseme)
                    trusttitle = searchObj.group()
                if re.search(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)?(?= TRUST)', parseme):
                    searchObj = re.search(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)?(?= TRUST)', parseme)
                    parseme = re.sub(r'((:? ?)(?:IR)?REVOC(?:ABLE)?)?(?= TRUST)', '', parseme)
                if re.search(r'REAL ESTATE TRUST', parseme):
                    searchObj = re.search(r'REAL ESTATE TRUST', parseme)
                    parseme = re.sub(r'REAL ESTATE TRUST', r'', parseme)
                    trusttitle = searchObj.group()
                if parseme.count(',') >= 2:
                # we've got something weird like SMITH, KEVIN, JAMES
                    parseme = re.sub(',', ' ', parseme)  # get rid of commas
                    parseme = re.sub('  ', ' ', parseme)
                    parseme = parseme.replace(' ', ', ', 1)  # replace the first occurrence of a space with a comma
                parsedname = HumanName(parseme)
                parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                            ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                            parsedname.nickname.title() + ' ' + trusttitle.title()
                parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 256:  # trustee
            parseme = re.sub(r' ?-? *-?\(? ?(?:CO)? ?-? ?TR(?:USTEE)?(?:S)?\)?', r'', parseme)
            parseme = re.sub(r' ?-?(\(SUCCESSOR)? ?(FOR)? ?(ESQ)? \(??TRUSTEE\)? ?\(?(ATTORNEY)?\)?', r'', parseme)
            parseme = re.sub(r'\bTR\b', '', parseme)
            parseme = re.sub(r'\b ?OF THE', '', parseme)
            if re.search(r'DATED(.*)', parseme) is not None:
                parseme = ''
                continue
            if re.search(r'AS TRUSTEE FOR', parseme) is not None or re.search(r'ASFOR', parseme) is not None:
                parseme = ''
                continue
            if parseme.count(',') == 0:
                parseme = parseme.replace(' ', ', ', 1)  # it seems like trustees are messed up in some counties and need a comma to work
            if parseme.count(',') >= 2:
                parseme = parseme.replace(',', ' ')
                parseme = parseme.replace(' ', ',', 1)
            if myval == 256:
                parsedname = HumanName(parseme)
                parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                            ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                            parsedname.nickname.title() + ' ' + '(Trustee)'
            else:
                parseme = parseme + ' (Trustee)'
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 384:  # trust and trustee so we need to separate them out
            if re.search(r'^TRUSTEE OF', parseme) is not None:  # found something that starts with trustee of
                parseme = re.sub(r'^TRUSTEE OF (.*)', r'\1', parseme)  # sets parseme to just the name of the trust
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 386:  # trust, trustee, and company
            parseme = re.sub(r'(?:, )?TRUSTEE', '', parseme)
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 512:  # attorney
            parseme = re.sub(r'\(? ?ESQ\.?\)?', r'', parseme)
            parseme = re.sub(r'\(? ?ATTORNEY ?\)?', r'', parseme)
            parsedname = HumanName(parseme)
            parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                      ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                      parsedname.nickname.title() + ' ' + '(Attorney)'
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 514:  # attorney
            parseme = re.sub(r'\(? ?ESQ\.?\)?', r'', parseme)
            parseme = re.sub(r'\(? ?ATTORNEY ?\)?', r'', parseme)
            parseme = re.sub(r',? ?ATTY(?:-IN-FACT)?', r'', parseme)
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 642:  # attorney AND trustee
            parseme = re.sub(r'INC,?', 'Inc', parseme)
            parseme = parseme.replace(',', '')
            parseme = re.sub(r'ATTY-IN-FACT', '(Attorney-in-Fact)', parseme)
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        elif myval == 768:  # attorney AND trustee
            parseme = re.sub(r'\(? ?ESQ\.?\)?', r'', parseme)
            parseme = re.sub(r'\(? ?ATTORNEY ?\)?', r'', parseme)
            parseme = re.sub(r' ?-? *-?\(? ?(?:CO)? ?-? ?TR(?:USTEE)?(?:S)?\)?', r'', parseme)
            parseme = re.sub(r' ?-?(\(SUCCESSOR)? ?(FOR)? ?(ESQ)? \(??TRUSTEE\)? ?\(?(ATTORNEY)?\)?', r'', parseme)
            parseme = re.sub(r'\bTR\b', '', parseme)
            parsedname = HumanName(parseme)
            parseme = parsedname.last.upper() + ' ' + parsedname.first.title() + ' ' + parsedname.middle.title() + \
                        ' ' + parsedname.title.title() + ' ' + parsedname.suffix.title() + ' ' + \
                        parsedname.nickname.title() + ' ' + '(Attorney) (Trustee)'
            parsedname = parseme
            if len(parsedname) > 0:
                goodparse.append(parsedname)

        else:  # a combination of two or more of the above and needs to be excepted
            print('PARSING ERROR:', parseme, 'return value =', whoami(parseme))
            parsedname = parseme

        if debugging == 'Y':
            print('return value =', myval, parseme, '-/-', deedtype, county)

    parsedname = ''
    goodparse = list(set(goodparse))
    x = 0
    while x <= len(goodparse) - 1:
        if goodparse[x] is None or goodparse[x] == '\x00':
            del goodparse[x]
        else:
            x = x + 1
    if len(goodparse) >= 3:
        for index, x in enumerate(goodparse):
            if index == 0:
                parsedname = x
            elif index <= len(goodparse) - 2:
                parsedname = parsedname + ',  ' + x
            elif index == len(goodparse) - 1:
                parsedname = parsedname + ', and ' + x
            else:
                parsedname = parsedname + x
    if len(goodparse) == 2:
        parsedname = goodparse[0] + ' and ' + goodparse[1]
    if len(goodparse) == 1:
        parsedname = goodparse[0]

    parsedname = ' '.join(parsedname.split())
    parsedname = re.sub(r' , ', ', ', parsedname)
    print('parsedname =', parsedname)

    # this is where we have to check on certain things for proper punctuation

    # end for
    return parsedname


def regtitle(match):
    match = match.group().title()
    return match


def regupper(match):
    match = match.group().upper()
    return match


def scrape():
    inputfile = open(inputfilename, 'r')
    url = inputfile.readline()
    counter = 0
    intfile = open(intfilename, 'w')
    firsttime = True

    while url != '':
        counter = counter + 1
        if firsttime:
            dots = 0
#            print('Reading file to get urls')
            firsttime = False
        else:
            dots = dots + 1
#            sys.stdout.write('.')
#            sys.stdout.flush()
            if dots % 80 == 0:
                print('')
        if url[:4] != 'http':
            # we're reading a county name
            county = url[:-1]
        else:
            # start of scrape
            r = requests.get(url)
            print(url)
            if r.status_code == 500:
                url = url[:-1]
                r = requests.get(url)
            soup = BeautifulSoup(r.text, 'lxml')
            table = soup.table  # find the table references

            for br in table.find_all('br'):  # finds the <br> and replaces with newlines (for the names)
                br.replace_with('\n')

            table_rows = table.find_all('tr')  # returns a list of table rows
            for tr in table_rows:
                td = tr.find_all('td')  # finds the table data
                row = [i.text for i in td]  # returns a list of data in each row from NDO. row is type list.
                if len(row) == 0:
                    intfile.write(county + '\n')
                else:
                    intfile.write(str(row) + '\n')
        url = inputfile.readline()
    inputfile.close()
    intfile.close()


def whoami(name):

    splitlist = name.split(' ')
    returnvalue = 0

    # find banks first
    if re.search(r'\bBANK\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'ECON(OMIC)? ?DEV(ELOPMENT)?', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bFSA\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'FARM (CREDIT )?SERVICE', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bHOUSING\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bLENDING\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bMERS\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bMORTGAGE\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'NEBR(ASKA)? ?INV(ESTMENT)? ?FIN(ANCE)? ?AUTH(ORITY)?', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'QUICKEN LOANS', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bSAVINGS\b', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'TITLE INS(URANCE)?', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'(U)(?:NITED)? ?(S)(?:TATE(S)?) ?(A)?', name) is not None:
        returnvalue = returnvalue + 1
    elif re.search(r'\bU\.?S\.? ?(D)?(EPT|EPARTMENT)?\.?(A)?\.? ?(OF)? ?(AG)?(RICULTURE)?', name) is not None:
        returnvalue = returnvalue + 1
    else:
        pass

    # find businesses
    if re.search(r'(?<!FARM SERVICE )AGENCY', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bCHURCH\b', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'CO(MPANY)?(?! PERS(ONAL)? REP(RESENTATIVE)?)\b', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bCORP(ORATION)?\b', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'(?<!US )DEP((T)|(ARTMENT))?\b', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bFARMS\b', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bINC(ORPORATED)?', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bLL(C|P)', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bLTD', name) is not None:
        returnvalue = returnvalue + 2
    elif re.search(r'\bPC', name) is not None:
        returnvalue = returnvalue + 2
    else:
        pass

    # find cities
    if re.search(r'CITY OF', name) is not None:
        returnvalue = returnvalue + 4

    # find counties
    if re.search(r'COUNTY(?! BANK)', name) is not None:
        returnvalue = returnvalue + 8

    # find credit unions
    if re.search(r'\bF?CU\b', name) is not None:
        returnvalue = returnvalue + 16
    elif re.search(r'CREDIT UNION', name) is not None:
        returnvalue = returnvalue + 16
    else:
        pass

    # find estates
    if re.search(r'\bDEC(EASE)?D', name) is not None:
        returnvalue = returnvalue + 32
    elif re.search(r'\b\(?ESTATE\)?', name) is not None:
        returnvalue = returnvalue + 32
    else:
        pass

    # find personal reps
    if re.search(r'(?:CO ?-?)?(P(?:ER)?(?:S)?(?:ONAL)? ?R(?:EP)(?:RESENTATIVE(?:S)?)?|\bPR\b)', name) is not None:
        returnvalue = returnvalue + 64


    # find trusts
    if returnvalue != 1 and returnvalue != 3:  # if it comes back as a bank and a business, we don't want it to be a trust
        if re.search(r'(?<!IN )TRUST[^E]', name) is not None:
            returnvalue = returnvalue + 128
        elif re.search(r'(?<!BANK & )TRUST\b', name) is not None:
            returnvalue = returnvalue + 128
        elif re.search(r'REAL ESTATE TRUST', name) is not None:
            returnvalue = returnvalue + 128
        else:
            pass

    # find trustees
    if re.search(r'(?:SUC(?:CESSOR )|(CO-)?)?(?:TR)(?=(USTEE))|TR\b|(SUC )|CO-|(SUC\.)', name) is not None:
        returnvalue = returnvalue + 256

    # find attorneys
    if re.search(r'\(?((?:ATT)(?:ORNE)?(?:Y)|(?:ESQ)\.?)\)?', name) is not None:
        returnvalue = returnvalue + 512

    return returnvalue

# main program starts here
tilde = '~'
debugging = input('Do you want to run in debugging mode? ').upper()
if debugging == 'Y':
    linestoskip = int(input('Lines to skip: '))

# The following triple quotes prevent having to rerun the scraper each time during debugging
if debugging != 'Y':
    defaultdate = getdefaultdate()
    print('If no file name entered, ' + defaultdate + '.txt will be used.')
    inputfilename = input('Enter name of input file: ')
    if not inputfilename:
        inputfilename = defaultdate + '.txt'
    if inputfilename[-3:] != 'txt':
        inputfilename = inputfilename + '.txt'

deedfilename = 'propertydeeds.csv'
releasefilename = 'releases.csv'
exceptionfilename = 'exceptions.csv'
intfilename = 'intfile.txt'
datafilename = 'datafile.txt'

# end debugging

"""
    The inputfile will be structured as follows:
    The first line will contain a county name.
    The next line(s) for that county will contain the URL for the data pages to be scraped.
    In the event that a given URL has more than 20 entries on the page, it will be necessary to enter the second
    page manually, or if possible, to just limit the amount of data passed by the URL.
    In order to make the URLs conform as nearly as possible to the pages that will be requested to enter monetary
    date, it is recommended that the most recent data be at the top of the URL list for a given county and the older
    data be towards the bottom.
    Example:
    countyname
    Friday's URL
    Thursday's URL
    Wednesday's URL
    Tuesday's URL
    Monday's URL
"""

# start the scrape
# commented out for debugging purposes. otherwise, it works.
if debugging != 'Y':
    scrape()

# all data is now in the intfile.txt file
# now we have to open the intfile as read-only and prepare to write to the datafile after necessary changes are made
fixint()

# this is where the actual data splitting occurs
datasplitter()


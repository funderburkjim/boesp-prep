# coding=utf-8
""" make_xml.py  Version from step3. Begun 12-01-2021.
 
"""
from __future__ import print_function
#import xml.etree.ElementTree as ET
import sys, re,codecs

def get_L_from_D(line):
 """
  Assume line contains one or more <Dn>
  Return list of all n
 """
 a = []
 for m in  re.finditer(r'<D([0-9]+)>',line):
  a.append(m.group(1))
 return a

def get_A_from_D(line):
 """
  Assume line starts with one or more <Dn>
  Return list of all n
 """
 a = []
 for m in  re.finditer(r'<A([0-9]+)>',line):
  a.append(m.group(1))
 return a

class Entry(object):
 def __init__(self,grouplist,page):
  self.groups = grouplist
  self.page = page  # page reference (1.n) where <S> starts
  #self.entrylines = entrylines(grouplist)
  # compute tags and Ls (some groups have more than 1 <Dx>
  Ls = []
  a = []
  for igroup,group in enumerate(self.groups):
   # group is a sequence of lines from boesp
   firstline = group[0]
   m = re.search(r'^<(.*?)>(.*)$',firstline)
   if not m:
    a.append('X')
   else:
    tag = m.group(1)
    rest = m.group(2)
    #if tag.startswith('F'):print(firstline)
    if tag.startswith('D'):
     # there may be multiple <DX><DY> in line Example <D145> 146.
     a.append('D')
     Lvals = get_L_from_D(firstline)
     Ls = Ls + Lvals
    elif tag.startswith('F') and ('DUMMY' in rest):
     tag = 'FDUMMY'
     a.append(tag)
     # also, alter
     group[0] = group[0].replace('<F>','<FDUMMY>')
     self.groups[igroup][0] = group[0]
     #print('dbg: group=',group)
     #exit(1)
    else:
     a.append(tag)
  self.Ls = Ls
  self.tags = a
  
def xml_header(xmlroot):
 # write header lines
 text = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE %s SYSTEM "%s.dtd">
<!-- <H> Boehtlingk, Indische Sprüche, 2. Auflage, St. Petersburg 1870 -->
<%s>
""" % (xmlroot,xmlroot,xmlroot)
 lines = text.splitlines()
 lines = [x.strip() for x in lines if x.strip()!='']
 return lines

def generate_groups(lines):
 iline = 0 # start at first line
 nlines = len(lines)
 # ignore blank lines
 while iline < nlines:
  while (lines[iline].strip() == ''):
   iline = iline + 1
   if iline == nlines:
    return []  # yield [] gives error
  # gather block of non-blank lines
  group = []
  while (lines[iline].strip() != ''):
   group.append(lines[iline])
   iline = iline + 1
   if iline == nlines:
    break
  yield group

def entrysummary(entry):
 gtypes = ','.join(entry.tags)
 page = entry.page # page on which entry starts
 Ls = entry.Ls
 if len(Ls) == 0:
  L = '?'
 else:
  L = ','.join(Ls)
 #text = 'L=%s: %s %s' %(L,gtypes,page)
 text = 'L="%s" page="%s" gtypes="%s"'%(L,page,gtypes)
 return text


def make_xml_S(group,entry):
 # group is a list of lines
 dbg = False
 Ds = entry.Ls
 outarr = []
 # At this point (with 12-01-2021), we ASSUME the <S> text is
 # note cases with {# or #} in Sanskrit text.
 # These will need to be reformated
 line0 = group[0][len('<S>'):]
 line0 = line0.lstrip()
 lines = group_to_lines(group,line0)
 outarr.append('<S>')
 for line in lines:
  outarr.append(line)
 outarr.append('</S>')
 return outarr

def curly_to_s(text):
 text = text.replace('{#','<s>')
 text = text.replace('#}','</s>')
 return text

def curly_to_i(text):
 text = text.replace('{%','<i>')
 text = text.replace('%}','</i>')
 return text

def curly_to_wide(text):
 text = text.replace('{|','<wide>')
 text = text.replace('|}','</wide>')
 return text

def curly_to_xml(text):
 text = curly_to_s(text)
 text = curly_to_i(text)
 text = curly_to_wide(text)
 # also, change [SeiteX] to <pb n="X"/>
 text = re.sub(r'\[Seite(.*?)\]',r'<pb n="\1"/>',text)
 # also, change [pageX] to <pb1 n="X"/>
 text = re.sub(r'\[Page(.*?)\]',r'<pb1 n="\1"/>',text)
 return text

def make_xml_D(group,entry):
 # group is a list of lines
 outarr = []
 #text = ' '.join(group)
 Ls = get_L_from_D(group[0]) # list of strings
 As = get_A_from_D(group[0])
 # reformat the <D> and <A> tags as bold text
 line0 = group[0]
 #line0 = re.sub(r'<D([0-9]+)>',r'<b>\1.</b> ',line0)
 Dtext = ' '.join(['<b>%s.</b>' % L for L in Ls])
 if As != []:
  Atext = ' '.join(['<b>%s.</b>' % L for L in As])
  # and add enclosing parens
  Atext = ' (%s)' % Atext
 else:
  Atext = ' '
 line0 = re.sub(r'<D.*?>','',line0)
 line0 = re.sub(r'<A.*?>','',line0)
 line0 = Dtext + Atext + line0
 lines = group_to_lines(group,line0)
 L = ','.join(Ls)
 A = ','.join(As)
 if As == []:
  outarr.append('<D n="%s">' % L)
 else:  
  outarr.append('<D n="%s" a="%s">' % (L,A))
 for line in lines:
  outarr.append(line)
 outarr.append('</D>')
 return outarr

def group_to_lines(group,line0):
 lines = []
 for iline,line in enumerate(group):
  if iline == 0:
   line = line0
  line = curly_to_xml(line)
  lines.append(line)
 return lines

def make_xml_F(group,entry):
 # group is a list of lines
 outarr = []
 m = re.search(r'^<F>([0-9.]+)\) (.*)$',group[0])
 if m == None:
  print('F problem:',group[0])
  exit(1)
 tag = 'F'
 Dnum = m.group(1)  # 67.68.69
 rest = m.group(2)  # if DUMMY, then mark as <FDUMMY>
 isdummy = (rest == 'DUMMY')
 Ds = Dnum.split('.')
 #Ds = [Dnum]
 line0 = group[0][len('<F>'):]
 
 lines = group_to_lines(group,line0)
 attrib = ','.join(Ds)
 if isdummy:
  outarr.append('<%s n="%s">' % ('FDUMMY',attrib))
 else:
  outarr.append('<%s n="%s">' % (tag,attrib))
 for line in lines:
  outarr.append(line)
 if isdummy:
  outarr.append('</FDUMMY>')
 else:
  outarr.append('</F>')
 return outarr

def make_xml_FDUMMY(group,entry):
 # group is a list of lines
 # group has one line, like '<F>'
 # we recast as '<FDUMMY>' Later we will delete or otherwise ignore this elt.
 outarr = []
 m = re.search(r'^<FDUMMY>([0-9.]+)\) (.*)$',group[0])
 if m == None:
  print('FDUMMY problem:',group[0])
  exit(1)
 tag = 'FDUMMY'
 Dnum = m.group(1)  # 67.68.69
 rest = m.group(2)  # if DUMMY, then mark as <FDUMMY>
 isdummy = (rest == 'DUMMY')
 Ds = Dnum.split('.')
 #Ds = [Dnum]
 line0 = group[0][len('<FDUMMY>'):] 
 lines = group_to_lines(group,line0)
 attrib = ','.join(Ds)
 outarr.append('<%s n="%s">' % ('FDUMMY',attrib))
 for line in lines:
  outarr.append(line)
 outarr.append('</FDUMMY>')
 return outarr

def make_xml_V123(group,entry):
 # group is a list of lines
 # group format is <V1>nnn. (or V2, V3)
 outarr = []
 #text = '\n'.join(group)
 m = re.search(r'^<(V[123])>([0-9]+)[.] (.*)$',group[0])
 if m == None:
  print('V123 ERROR: ',group[0])
  exit(1)
 tag = m.group(1)
 Dnum = m.group(2)
 Ds = [Dnum]
 line0 = '%s. %s' %(m.group(2), m.group(3))
 lines = group_to_lines(group,line0)
 attrib = ','.join(Ds)  # Ds has just one for V
 outarr.append('<%s n="%s">' % (tag,attrib))
 for line in lines:
  outarr.append(line)
 outarr.append('</%s>' % tag)
 return outarr

def F412_dnum_special(line):
 starts = [
  ('<F4.1>-- S. 624, Z. 9' , '777'),
  ('<F4.1>-- S. 633, Spr. 2152' , '2152'),
  ('<F4.1>-- S. 639, Z. 2' , '3187'),
  ('<F4.1>-- S. 641, Spr. 3754' , '3754'),
  ('<F4.1>-- Spr. 3791, Z. 2' , '3791'),
  ('<F4.1>-- S. 642, Spr. 3979' , '3979'),
  ('<F4.1>-- S. 643, Spr. 4116' , '4116'),
  ('<F4.1>-- S. 647, Spr. 5589, Z. 2' , '5589'),
  ('<F4.2>6390-6392 ' , '6390'),
  ('<F4.1>-- S. 649, Spr. 6528, Z. 3' , '6528'),
  ('<F4.1>-- S. 539, Z. 4' , '7224'),
 ]
 for text,dnum in starts:
  if line.startswith(text):
   return dnum
 print('F4142_dnum_special fails for line:')
 print(line)
 exit(1)
 return None

def make_xml_F412(group,entry):
 # group is a list of lines
 # group format is <F4.1>-- nnn. (or F4.2)  (in one have 6390-6392 for nnn)
 # except for 10 cases of form S. --- We handle these in separate function
 outarr = []
 m = re.search(r'^<(F4[.][12])>',group[0])
 tag = m.group(1)
 m = re.search(r'^<(F4[.][12])>-- ([0-9]+)(.*)$',group[0])
 if m == None:
  Dnum = F412_dnum_special(group[0])
 else:
  Dnum = m.group(2)
 Ds = [Dnum]
 line0 = group[0][len('<F4.1>'):]
 lines = group_to_lines(group,line0)
 attrib = ','.join(Ds)  # Ds has just one for V
 outarr.append('<%s n="%s">' % (tag,attrib))
 for line in lines:
  outarr.append(line)
 outarr.append('</%s>' % tag)
 return outarr

def make_xml_HS(group,entry):
 # group is a list of lines
 # Here, the printed text is always (I think) in one line.
 # And we construct this similarly.
 # We also do NOT adjust the line lengths
 outarr = []
 text = ' '.join(group)
 # remove the HS tag
 text = re.sub(r'^<HS>','',text)
 text = text.strip()
 text = curly_to_xml(text)
 text = re.sub(r'  +',' ',text) # remove extra spaces
 lines = [text]
 outarr.append('<HS>')
 assert (len(lines) == 1)
 for line in lines:
  outarr.append(line)
 outarr.append('</HS>')
 return outarr

def make_xml_H(group,entry):
 # group is a list of lines
 # only 3 cases. Each has one line. Replace with an xml comment
 # completely skip these groups
 line = '<!-- %s -->' % group[0]
 outarr = [line]
 return outarr

def make_xml_unknown(group,entry):
 # group is a list of lines. Only 1 instance
 # The tag is unknown
 # print with X 
 outarr = []
 outarr.append('<X>')
 for line in group:
  outarr.append(line)
 outarr.append('</X>')
 return outarr

def test_S_prep(a):
 # a is array of strings
 b = []
 for x in a:
  x = x.strip()
  x = re.sub(r'  +',' ',x)
  b.append(x)
 return b

def test_S(outgroup,outgroup1,entry):
 #compare to ways to compute the lines for <S>
 # use difflib 
 lines = test_S_prep(outgroup)
 lines1 = test_S_prep(outgroup1)
 import difflib
 d = difflib.Differ()
 diff = d.compare(lines,lines1)
 print('\n' .join(diff))
 exit(1)
 
def entrylines(entry,tranin):
 outarr = []
 outarr.append('') # blank line separates entries. Non-essential.
 outarr.append('<entry>')
 text = entrysummary(entry)
 outarr.append('<info %s/>' %text)
 for igroup,group in enumerate(entry.groups):
  tag = entry.tags[igroup]
  if tag == 'S':
   outgroup = make_xml_S(group,entry)
  elif tag == 'D':
   outgroup = make_xml_D(group,entry)
  elif tag == 'F':
   outgroup = make_xml_F(group,entry)
  elif tag == 'FDUMMY':
   outgroup = make_xml_FDUMMY(group,entry)
  elif tag in ['V1','V2','V3']:
   outgroup = make_xml_V123(group,entry)
  elif tag in ['F4.1','F4.2']:
   outgroup = make_xml_F412(group,entry)
  elif tag == 'HS':
   outgroup = make_xml_HS(group,entry)
  elif tag == 'H':
   outgroup = make_xml_H(group,entry)
  else:
   #print('unknown tag:',tag)
   outgroup = make_xml_unknown(group,entry)
  for x in outgroup:
   outarr.append(x)
 outarr.append('</entry>')
 return outarr
 
def updatepage(entry,page):
 for group in entry:
  for line in group:
   m = re.search(r'\[Seite([0-9][.][0-9]+)\]',line)
   if m:
    newpage = m.group(1)
    return newpage
 return page # no change

def generate_entries(lines):
 ngroup = 0
 #nentry = 0
 firstfound = False
 page = '1.1'
 for group in generate_groups(lines):
  ngroup = ngroup+1
  # skip the groups until a condition is met
  if firstfound:
   if group[0].startswith('<S>'):
    if entry != []:
     e = Entry(entry,page)
     page = updatepage(entry,page)  # for next entry
     yield e
    entry = [group] # start a new group
   else:
    entry.append(group)
  elif group[0].startswith('<H> Boehtlingk'):
   firstfound = True
   entry = []
 yield Entry(entry,page)

def xml_body(entries,tranin):
 # generate xml header lines
 body = []
 nentry = 0
 for entry in entries:
  outarr = entrylines(entry,tranin)
  nentry = nentry + 1
  for out in outarr:
   body.append(out)
 print(nentry,'entries found')
 return body

def check_L(entries):
 # check sequencing of L-valuese of entries.  Print aberrations
 Lprev = None
 nprob = 0
 for ientry,entry in enumerate(entries):
  Ls = entry.Ls
  #print('Ls=',Ls)
  if Ls == []:
   print('ERROR: No L. previous = ',Lprev)
   continue
  L = int(Ls[0])
  if ientry == 0:
   Lprev = L
  elif L != (Lprev + 1):
   print('Sequencing problem at entry %s: %s should be %s'%(ientry+1,L,Lprev+1))
   # sequence comes from <DN>, in first line of second group of entry
   dgroup = entry.groups[1]
   old = dgroup[0]
   dold = '<D%s>' % L
   Lnew = Lprev+1
   dnew = '<D%s>' % Lnew
   new = old.replace(dold,dnew)
   print(old)
   print(new)
   print()
   Lprev = int(Ls[-1])
   nprob = nprob + 1
   if nprob == 5:
    print('quitting after 5 problems')
    return
  else:
   Lprev = int(Ls[-1])

def check_tagsequence(entries):
 d = {}
 for entry in entries:
  tagseq = ','.join(entry.tags)
  if tagseq not in d:
   d[tagseq] = 0
  d[tagseq] = d[tagseq] + 1
 keys = d.keys()
 for tagseq in keys:
  print('%04d %s' %(d[tagseq],tagseq))

def check_tagfreq(entries):
 d = {}
 for entry in entries:
  for tag in entry.tags:
   if tag not in d:
    d[tag] = 0
   d[tag] = d[tag] + 1
 keys = d.keys()
 for tag in keys:
  print('%04d %s' %(d[tag],tag))

def check_page(entries):
 nprob = 0
 for ientry,entry in enumerate(entries):
  page = entry.page
  v,p = page.split('.')
  if ientry == 0:
   p0 = p
  elif p0 == p:
   pass
  elif int(p) == (int(p0)+1):
   p0 = p
  else:
   text = entrysummary(entry)
   print('page problem: ',text,' p0=%s, p=%s'% (p0,p))
   nprob = nprob + 1
 print('check_page found %s problems' %nprob)

def check_san(entries):
 nprob = 0
 for ientry,entry in enumerate(entries):
  for group in entry.groups:
   text = ' '.join(group)
   n1 = len(re.findall('{#',text))
   n2 = len(re.findall('#}',text))
   if n1 != n2:
    text = entrysummary(entry)
    print('unbalanced {#..#} ',text)
    nprob = nprob + 1
 print('check_san found %s problems' %nprob)

def statistics(entries):
 check_L(entries)
 # check_tagsequence(entries)
 check_tagfreq(entries)
 check_page(entries)
 check_san(entries)

def entries_HS_adjust(entries):
 """ HS entries are known to occur at the END of groups
  However, they seem to belong to the NEXT group.
  This routine makes the blanket change of entries thus indicated.
  That is, if an entry ends with one or more HS items, then we
  remove these and put them at the beginning of the next entry.

 """
 dbg = False
 for ientry,entry in enumerate(entries):
  oldtags = entry.tags
  ntags = len(oldtags)
  hsend = ntags - 1
  if 'HS' != oldtags[hsend]:
   continue
  #oldgroups = entry.groups not used
  while True:
   hsend1 = hsend - 1
   if oldtags[hsend1] == 'HS':
    hsend = hsend1
   else:
    break
  #  So when hsend <= idx < ntags, tags[idx] = HS
  idxkeep = [i for i in range(len(entry.groups)) if i < hsend]
  idxdrop = [i for i in range(len(entry.groups)) if hsend <= i]
  groups = [entry.groups[i] for i in idxkeep]
  tags = [entry.tags[i] for i in idxkeep]
  #
  groups1 = [entry.groups[i] for i in idxdrop]
  tags1 = [entry.tags[i] for i in idxdrop]
  # change entry.groups and tags
  entry.groups = groups
  entry.tags = tags
  # now also modify the next entry
  ientry1 = ientry+1
  if ientry1 == len(entries):
   print('entries_HS_adjust anomaly:',entrysummary(entry))
   continue
  entry1 = entries[ientry+1]
  if dbg: print('old1:',ientry1,entrysummary(entry1))
  entry1.groups = groups1 + entry1.groups
  entry1.tags = tags1 + entry1.tags
  # The page number for the entry1 should be that for entry
  entry1.page = entry.page  # only line changed
  entries[ientry1] = entry1
def read_and_clean_lines(filein):
 with codecs.open(filein,encoding='utf-8',mode='r') as f:
  nprob = 0
  lines = []
  for iline,line in enumerate(f):
   line = line.rstrip('\r\n')
   # cleaning <>
   if '<>' in line:
    nprob = nprob + 1
    line = line.replace('<>','')
   # remove middledot+space at end of lines.
   line = re.sub(r'· $','',line)
   if '·' in line:
    print('malformed use of middle dot at line',iline+1)
    nprob = nprob + 1
   lines.append(line)
   
 print(len(lines),"lines read from",filein)
 
 if nprob != 0:
  print('read_and_clean_lines:',nprob,'problems need to be fixed')
  exit(1)
 return lines

if __name__=="__main__":
 tranin = 'hk'

 filein = sys.argv[1] # boesp_utf8.txt
 fileout = sys.argv[2] # boesp-hk.xml
 xmlroot = 'boesp'
 lines = read_and_clean_lines(filein)
    
 head = xml_header(xmlroot)
 entries = list(generate_entries(lines))
 entries_HS_adjust(entries)
 body = xml_body(entries,tranin)
 tail = ['</%s>'%xmlroot]
 linesout = head + body  + tail
 with codecs.open(fileout,"w","utf-8") as f:
  for line in linesout:
   f.write(line+'\n')
 #statistics(entries)
 

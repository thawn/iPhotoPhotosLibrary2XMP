import sqlite3
import os.path

database_file = 'photos.db'
library_path = os.path.join(os.path.expanduser("~"), 'Pictures')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--path', '--library-path', default=library_path, help='path to your iPhoto/Photos library')
    args = ap.parse_args()
    library_path = args.path
    if 'iPhoto' in library_path:
        database_file = os.path.join(library_path, 'Database', 'apdb', 'Library.apdb')
    elif 'Photos Library' in library_path:
        database_file = os.path.join(library_path, 'database', 'photos.db')        


xmp_template = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:darktable="http://darktable.sf.net/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"
   xmp:Rating="{rating}"
   xmpMM:DerivedFrom="{filename}"
   darktable:xmp_version="2"
   darktable:raw_params="0"
   darktable:auto_presets_applied="0"
   darktable:history_end="0">
   <darktable:mask_id>
    <rdf:Seq/>
   </darktable:mask_id>
   <darktable:mask_type>
    <rdf:Seq/>
   </darktable:mask_type>
   <darktable:mask_name>
    <rdf:Seq/>
   </darktable:mask_name>
   <darktable:mask_version>
    <rdf:Seq/>
   </darktable:mask_version>
   <darktable:mask>
    <rdf:Seq/>
   </darktable:mask>
   <darktable:mask_nb>
    <rdf:Seq/>
   </darktable:mask_nb>
   <darktable:mask_src>
    <rdf:Seq/>
   </darktable:mask_src>
   <darktable:history>
    <rdf:Seq/>
   </darktable:history>
{keywords}  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>

'''
keyword_section = '''   <dc:subject>
    <rdf:Seq>
{keywords}    </rdf:Seq>
   </dc:subject>
   <lr:hierarchicalSubject>
    <rdf:Seq>
{keywords}    </rdf:Seq>
   </lr:hierarchicalSubject>
'''

conn = sqlite3.connect(database_file)
c = conn.cursor()
#c.execute('SELECT RKVolume.name,RKMaster.imagePath,RKMaster.fileName FROM RKMaster JOIN RKVolume ON RKMaster.volumeId=RKVolume.modelId' )
if database_file.endswith('.apdb'):
    volume_join = 'd.fileVolumeUuid=RKVolume.uuid'
else:
    volume_join = 'd.volumeId=RKVolume.modelId'
data_query = 'SELECT m.imagePath, m.fileName, m.fileVolumeUuid, m.volumeId, v.modelId, v.mainRating, v.versionNumber, v.hasKeywords FROM RKMaster m JOIN RKVersion v ON m.modelId = v.masterId WHERE (v.mainRating > 0 OR v.hasKeywords > 0)'
columns = 'd.modelId, RKVolume.name, d.imagePath, d.fileName, d.mainRating'
grouped_data = '(SELECT d.imagePath, MAX(d.versionNumber) AS maxVersion FROM d GROUP BY d.imagePath) gd ON d.imagePath = gd.imagePath AND d.versionNumber = gd.maxVersion'
c.execute('WITH d AS ({dq}) SELECT {col} FROM d JOIN {gd} JOIN RKVolume ON {vj}'.format(dq=data_query, col=columns, gd=grouped_data, vj=volume_join) )
all_rows = c.fetchall()
data = {}
for row in all_rows:
    filename = os.path.join('/Volumes', row[1], row[2]) + '.xmp'
    print('writing: ' + filename)
    rating = row[4]
    c.execute('SELECT k.name FROM RKKeyword k JOIN RKKeywordForVersion v ON k.modelId = v.keywordId WHERE v.versionId = ?', (row[0],))
    keyword_text = ''
    keywords = set()
    for tupl in c.fetchall():
        for keyword in tupl:
            if not keyword.endswith('Star'):
                keywords.add(keyword)
            else:
                if rating == 0:
                    rating = int(keyword[0])
    if keywords:
        keyword_list = ''
        for keyword in keywords:
            keyword_list += '     <rdf:li>{keyword}</rdf:li>\n'.format(keyword=keyword)
        keywords_text = keyword_section.format(keywords=keyword_list)
    with open(filename, 'w') as xmp_file:
        xmp_file.write(xmp_template.format(rating=str(rating), filename=row[3], keywords=keywords_text))    
conn.close()
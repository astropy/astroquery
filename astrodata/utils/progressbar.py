import urllib2, sys

__all__ = ['chunk_report','chunk_read']

def chunk_report(bytes_so_far, chunk_size, total_size):
    if total_size > 0:
        percent = float(bytes_so_far) / total_size
        percent = round(percent*100, 2)
        sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" % 
            (bytes_so_far, total_size, percent))
    else:
        sys.stdout.write("Downloaded %10.2g Mb\r" % 
            (bytes_so_far / 1024.**2))
  

def chunk_read(response, chunk_size=1024, report_hook=None):
    content_length = response.info().getheader('Content-Length')
    if content_length is None:
        total_size = 0
    else:
        total_size = content_length.strip()
        total_size = int(total_size)

    bytes_so_far = 0
  
    result_string = ""

    #sys.stdout.write("Beginning download.\n")
  
    while 1:
       chunk = response.read(chunk_size)
       result_string += chunk
       bytes_so_far += len(chunk)
  
       if not chunk:
           if report_hook: 
               sys.stdout.write('\n')
           break
  
       if report_hook:
          report_hook(bytes_so_far, chunk_size, total_size)
  
    return result_string

if __name__ == '__main__':
   response = urllib2.urlopen('http://www.ebay.com')
   C = chunk_read(response, report_hook=chunk_report)


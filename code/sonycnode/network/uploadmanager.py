import pycurl
import cStringIO
import weakref

from sonycnode.network.netmanager import getMac


class UploadManager(object):

    def __init__(self, ifacename, url, timeout,
                 secure=False, cacert=None, client_cert=None,
                 client_key=None, client_pass=None,
                 crlfile=None, **kwargs):
        """
        Paramters
        ---------
        ifacename: str
        iinterface that will be used for
        uploading data
        url: str
        url to upload the files to
        timeout: int
        seconds to wait before timing out
        secure: bool
        Whether to use HTTP or HTTPS
        .. note: `secure` will be default in the
        future releases and the flag will
        be removed
        cacert: str
        Absolute path for the CA certificate
        .. note: if secure=True, cacert should be provided
        client_cert: str, optional
        Absolute path for client's SSL certificate
        client_key: str, optional
        Absolute path for client's SSL key
        client_pass: str, optional
        Password for client's SSL cert
        crlfile: str, optional
        Certificate Revocation List file for checking 
        if the certificate has been revoked by CA
        Returns
        -------
        upload_status: tuple
        speed of upload, respone code from
        upload server
        """
        self.ifacename   = ifacename
        self.url         = url
        self.timeout     = timeout
        self.secure      = secure
        self.cacert      = cacert
        self.client_cert = client_cert
        self.client_key  = client_key
        self.client_pass = client_pass
        self.crlfile     = crlfile

    def __enter__(self):
        class Uploader(object):
            """
            Class to uploade file and Status
            """
            def __init__(self, ifacename, url, timeout,
                         secure=False, cacert=None, client_cert=None,
                         client_key=None, client_pass=None,
                         crlfile=None, **kwargs):
                
                self.curl = pycurl.Curl()
                self.curl.setopt(pycurl.URL, url)
                self.curl.setopt(pycurl.TIMEOUT, timeout)
                self.curl.setopt(
                    pycurl.HTTPHEADER, [
                        'id: ' + getMac(ifacename)])
                if secure:
                    # Use TLS v1.2
                    self.curl.setopt(
                        pycurl.SSLVERSION,
                        pycurl.SSLVERSION_DEFAULT)
                    self.curl.setopt(pycurl.SSL_VERIFYPEER, 1)
                    self.curl.setopt(pycurl.SSL_VERIFYHOST, 2)
                    self.curl.setopt(pycurl.CAINFO,
                                     cacert)
                                     
                    self.curl.setopt(pycurl.SSLCERT, client_cert)
                    
                    self.curl.setopt(pycurl.SSLKEY, client_key)
                    self.curl.setopt(pycurl.SSLKEYPASSWD, client_pass)
                    
                    if crlfile is not None:
                        self.curl.setopt(pycurl.CRLFILE, crlfile)
                    
                    # Make curl cookie-aware.. some serious BLACKMAGIC!!
                    self.curl.setopt(pycurl.COOKIEFILE, '')
                self.response = cStringIO.StringIO()

            def _info(self):
                """
                Return a dictionary with all info on the last response.
                """
                info = {}
                info['effective-url']           = self.curl.getinfo(pycurl.EFFECTIVE_URL)
                info['http-code']               = self.curl.getinfo(pycurl.HTTP_CODE)
                info['total-time']              = self.curl.getinfo(pycurl.TOTAL_TIME)
                info['namelookup-time']         = self.curl.getinfo(pycurl.NAMELOOKUP_TIME)
                info['connect-time']            = self.curl.getinfo(pycurl.CONNECT_TIME)
                info['pretransfer-time']        = self.curl.getinfo(pycurl.PRETRANSFER_TIME)
                info['redirect-time']           = self.curl.getinfo(pycurl.REDIRECT_TIME)
                info['redirect-count']          = self.curl.getinfo(pycurl.REDIRECT_COUNT)
                info['size-upload']             = self.curl.getinfo(pycurl.SIZE_UPLOAD)
                info['size-download']           = self.curl.getinfo(pycurl.SIZE_DOWNLOAD)
                info['speed-upload']            = self.curl.getinfo(pycurl.SPEED_UPLOAD)
                info['header-size']             = self.curl.getinfo(pycurl.HEADER_SIZE)
                info['request-size']            = self.curl.getinfo(pycurl.REQUEST_SIZE)
                info['content-type']            = self.curl.getinfo(pycurl.CONTENT_TYPE)
                info['response-code']           = self.curl.getinfo(pycurl.RESPONSE_CODE)
                info['speed-download']          = self.curl.getinfo(pycurl.SPEED_DOWNLOAD)
                info['ssl-verifyresult']        = self.curl.getinfo(pycurl.SSL_VERIFYRESULT)
                info['filetime']                = self.curl.getinfo(pycurl.INFO_FILETIME)
                info['starttransfer-time']      = self.curl.getinfo(pycurl.STARTTRANSFER_TIME)
                info['http-connectcode']        = self.curl.getinfo(pycurl.HTTP_CONNECTCODE)
                info['httpauth-avail']          = self.curl.getinfo(pycurl.HTTPAUTH_AVAIL)
                info['proxyauth-avail']         = self.curl.getinfo(pycurl.PROXYAUTH_AVAIL)
                info['os-errno']                = self.curl.getinfo(pycurl.OS_ERRNO)
                info['num-connects']            = self.curl.getinfo(pycurl.NUM_CONNECTS)
                info['ssl-engines']             = self.curl.getinfo(pycurl.SSL_ENGINES)
                info['cookielist']              = self.curl.getinfo(pycurl.INFO_COOKIELIST)
                info['lastsocket']              = self.curl.getinfo(pycurl.LASTSOCKET)
                info['server-response']         = self.response.getvalue()
                info['content-length-download'] = self.curl.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD)
                info['content-length-upload']   = self.curl.getinfo(pycurl.CONTENT_LENGTH_UPLOAD)
                # Close the connection
                self.curl.close()
                return info

            def uploadFile(self, filename):
                """
                Method to upload a file to the server
                using http(s) post request
                Parameters
                ----------
                filename: str
                Absolute path of the file to be uploaded
                Returns
                -------
                connection_info: dict
                Dictionary containing all the info related to transfer
                """
                self.curl.setopt(pycurl.POST, 1)
                self.curl.setopt(pycurl.HTTPPOST, [('file1', (pycurl.FORM_FILE,
                                                              filename))])
                self.curl.setopt(pycurl.WRITEFUNCTION, self.response.write)
                self.curl.perform()
                return self._info()
    
            def uploadStatus(self, status_dump):
                """
                Upload StatusPing messages
                Paramters
                ---------
                status_dump: str
                json dump of string
                .. note: you can use `json.dumps(<json formatted text>)`
                Returns
                -------
                connection_info: dict
                Dictionary containing all the info related to transfer
                """
                self.curl.setopt(pycurl.POST, 1)
                self.curl.setopt(pycurl.POSTFIELDS, status_dump)
                self.curl.setopt(pycurl.WRITEFUNCTION, self.response.write)
                self.curl.perform()
                return self._info()
            
            def cleanup(self):
                """
                Cleanup manually for sanity
                """
                if self.curl:
                    self.curl.close()
                    self.curl = None
                pycurl.global_cleanup()
                self.reponse = None

        self.uploader_obj = Uploader(self.ifacename,
                                     self.url,
                                     self.timeout,
                                     self.secure,
                                     self.cacert,
                                     self.client_cert,
                                     self.client_key,
                                     self.client_pass,
                                     self.crlfile)
        return weakref.ref(self.uploader_obj)()

    def __exit__(self, exc_type, exc_value, traceback):
        self.uploader_obj.cleanup()
        del self.uploader_obj

from astrometry.util.pyfits_utils import *
from numpy import *

# Reconstruct the SDSS model PSF from KL basis functions.
#   hdu: the psField hdu for the band you are looking at.
#      eg, for r-band:
#	     psfield = pyfits.open('psField-%06i-%i-%04i.fit' % (run,camcol,field))
#        bandnum = 'ugriz'.index('r')
#	     hdu = psfield[bandnum+1]
#
#   x,y can be scalars or 1-d numpy arrays.
# Return value:
#    if x,y are scalars: a PSF image
#    if x,y are arrays:  a list of PSF images
def sdss_psf_at_points(hdu, x, y):
	rtnscalar = isscalar(x) and isscalar(y)
	x = atleast_1d(x)
	y = atleast_1d(y)

	psf = table_fields(hdu.data)

	psfimgs = None
	(outh, outw) = (None,None)
	
	# From the IDL docs:
	# http://photo.astro.princeton.edu/photoop_doc.html#SDSS_PSF_RECON
	#   acoeff_k = SUM_i{ SUM_j{ (0.001*ROWC)^i * (0.001*COLC)^j * C_k_ij } }
	#   psfimage = SUM_k{ acoeff_k * RROWS_k }
	for k in range(len(psf)):
		nrb = psf.nrow_b[k]
		ncb = psf.ncol_b[k]

		#print 'c shape:', psf.c[k].shape
		c = psf.c[k].reshape(5, 5)
		c = c[:nrb,:ncb]

		(gridi,gridj) = meshgrid(range(nrb), range(ncb))

		if psfimgs is None:
			psfimgs = [zeros_like(psf.rrows[k]) for xy in broadcast(x,y)]
			(outh,outw) = (psf.rnrow[k], psf.rncol[k])
		else:
			assert(psf.rnrow[k] == outh)
			assert(psf.rncol[k] == outw)

		for i,(xi,yi) in enumerate(broadcast(x,y)):
			acoeff_k = sum(((0.001 * xi)**gridi * (0.001 * yi)**gridj * c))
			if False: # DEBUG
				print 'coeffs:', (0.001 * xi)**gridi * (0.001 * yi)**gridj
				print 'c:', c
				for (coi,ci) in zip(((0.001 * xi)**gridi * (0.001 * yi)**gridj).ravel(), c.ravel()):
					print 'co %g, c %g' % (coi,ci)
				print 'acoeff_k', acoeff_k
			psfimgs[i] += acoeff_k * psf.rrows[k]

	psfimgs = [img.reshape((outh,outw)) for img in psfimgs]

	if rtnscalar:
		return psfimgs[0]
	return psfimgs
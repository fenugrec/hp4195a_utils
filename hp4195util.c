/*
 * (c) fenugrec 2023
 *
 * GPLv3
 *
 * simple tool to work with ROM dumps from HP 4195A
 *
 * limited functionality. see usage (run without args)
 *
 *
 */

#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <getopt.h>

#include "stypes.h"


#define FONTTBL_START 0x9000	// font table is an array of pointers to char bitmaps
#define GLYPH_STARTOFFS -5	//bitmap data starts N bytes before the pointer target for some reason

#define FONTTBL_GLYPHS 0x80
#define GLYPH_BYTES	13	// rows
#define FONTTBL_SIZE (FONTTBL_GLYPHS * GLYPH_BYTES)

#define FILE_MAXSIZE (1*1024*1024UL)	//arbitrary 1MB sanity limit


uint32_t reconst_32(const uint8_t *buf) {
	// ret 4 bytes at *buf with SH endianness
	// " reconst_4B"
	return buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3];
}


// hax, get file length but restore position
static u32 flen(FILE *hf) {
	long siz;
	long orig;

	if (!hf) return 0;
	orig = ftell(hf);
	if (orig < 0) return 0;

	if (fseek(hf, 0, SEEK_END)) return 0;

	siz = ftell(hf);
	if (siz < 0) siz=0;
		//the rest of the code just won't work if siz = UINT32_MAX
	#if (LONG_MAX >= UINT32_MAX)
		if ((long long) siz == (long long) UINT32_MAX) siz = 0;
	#endif

	if (fseek(hf, orig, SEEK_SET)) return 0;
	return (u32) siz;
}


// ret 1 if ok
bool get_font(FILE *romfil, u8 fonttbl[FONTTBL_SIZE]) {
	u32 file_len;

	rewind(romfil);
	file_len = flen(romfil);
	if ((!file_len) || (file_len > FILE_MAXSIZE)) {
		printf("huge file (length %lu)\n", (unsigned long) file_len);
		return 0;
	}

	if (file_len <= (FONTTBL_START + FONTTBL_SIZE)) {
		printf("incomplete file ?\n");
		return 0;
	}

	u8 *src = malloc(file_len);
	if (!src) {
		printf("malloc choke\n");
		return 0;
	}

	/* load whole ROM */
	if (fread(src,1,file_len,romfil) != file_len) {
		printf("trouble reading\n");
		goto badexit;
	}


	unsigned file_ofs = FONTTBL_START;
	unsigned tbl_idx = 0;
	for (; tbl_idx < FONTTBL_GLYPHS; tbl_idx++) {
		u32 gl_ptr = reconst_32(&src[file_ofs + (4 * tbl_idx)]);
		u32 gl_start = gl_ptr + GLYPH_STARTOFFS;

		if (gl_start >= file_len) {
			printf("OOB glyph ptr %x\n", gl_start);
			goto badexit;
		}
		memcpy(&fonttbl[tbl_idx * GLYPH_BYTES], &src[gl_start], GLYPH_BYTES);
	}
	return 1;

badexit:
	if (src) free(src);
	return 0;
}



static struct option long_options[] = {
	{ "help", no_argument, 0, 'h' },
	{ NULL, 0, 0, 0 }
};

static void usage(void) {
	fprintf(stderr, "usage:\n"
		"\t-i <filename>\tbinary ROM dump\n"
		"\t-o <filename>\toutput file name\n"
		"");
}


int main(int argc, char * argv[]) {
	char c;

	int optidx;
	FILE *ifile = NULL;
	FILE *ofile = NULL;

	printf(	"************ hp4195util, "
		"(c) 2023 fenugrec ************\n");

	while((c = getopt_long(argc, argv, "i:o:h",
			       long_options, &optidx)) != -1) {
		switch(c) {
		case 'h':
			usage();
			return 0;
		case 'i':
			if (ifile) {
				fprintf(stderr, "-f given twice");
				goto bad_exit;
			}
			ifile = fopen(optarg, "rb");
			if (!ifile) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			break;
		case 'o':
			if (ofile) {
				fprintf(stderr, "-o given twice");
				goto bad_exit;
			}
			ofile = fopen(optarg, "wb");
			if (!ofile) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			break;
		default:
			usage();
			goto bad_exit;
		}
	}
	if (!ifile || !ofile) {
		printf("some missing args.\n");
		usage();
		goto bad_exit;
	}

	if (optind <= 1) {
		usage();
		goto bad_exit;
	}

	u8 fonttbl[FONTTBL_SIZE];
	if (get_font(ifile, fonttbl)) {
		fwrite(fonttbl, 1, FONTTBL_SIZE, ofile);
	}

	fclose(ifile);
	fclose(ofile);
	return 0;

bad_exit:
	if (ifile) fclose(ifile);
	if (ofile) fclose(ofile);
	return 1;
}

(load "69.scm")

(define lyric-symbols
  '((A 2)
    (GET 2)
    (SHA 3)
    (WAH 1)
    (BOOM 1)
    (JOB 2)
    (NA 16)
    (YIP 9)))

(define rock-song-huffman-tree
  (generate-huffman-tree
    lyric-symbols))

(define row-1 '(Get a job))
(define row-2 '(Sha na na na na na na na na))
(define row-3 row-1)
(define row-4 row-2)
(define row-5 '(Wah yip yip yip yip yip yip yip yip yip))
(define row-6 '(Sha boom))

(define lyric (append
                row-1
                row-2
                row-3
                row-4
                row-5
                row-6))

(define encoded-lyric
  (encode lyric rock-song-huffman-tree))

(define (ceiling-log2 x)
  (define (iter cur exponent)
    (if (< cur x)
        (iter (* 2 cur) (+ 1 exponent))
        exponent))
  (iter 1 0))

(newline)
(display "****************************************")
(newline)
(display "variable-length encoded lyric length: ")
(display (length encoded-lyric))
(newline)
(display "fixed-length encoded lyric length: ")
(display (* (ceiling-log2 (length lyric-symbols))
            (length lyric)))
(newline)
(display "****************************************")
(newline)

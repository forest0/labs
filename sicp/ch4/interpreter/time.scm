(define (time->string)
  (let ((cur-time (local-decoded-time)))
    (string-append (number->string (decoded-time/year cur-time))
                   "/"
                   (number->string (decoded-time/month cur-time))
                   "/"
                   (number->string (decoded-time/day cur-time))
                   " "
                   (number->string (decoded-time/hour cur-time))
                   ":"
                   (number->string (decoded-time/minute cur-time))
                   ":"
                   (number->string (decoded-time/second cur-time)))))

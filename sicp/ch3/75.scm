(define (make-zero-crossings input-stream last-value last-avpt)
  (let ((avpt (/ (+ (stream-car intput-stream)
                    last-value)
                 2)))
    (cons-stream
      (sign-change-detector apvt last-avpt)
      (make-zero-crossings
        (stream-cdr input-stream)
        (stream-car input-stream)
        avpt))))

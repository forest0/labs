(define (make-account balance password)
  (define (withdraw amount)
    (if (>= balance amount)
        (begin
          (set! balance (- balance amount))
          balance)
        "Insufficient funds"))

  (define (deposit amount)
    (set! balance (+ balance amount))
    balance)

  (define (try-password input-password)
    (eq? input-password password))

  (define (wrong-password-handler useless-arg)
    (display "Incorrect password"))


  (lambda (input-password op)
    (cond ((eq? op 'try-password) (try-password input-password))
          ((try-password input-password)
           (cond ((eq? op 'withdraw) withdraw)
                 ((eq? op 'deposit) deposit)
                 (else (error "Unknown request: MAKE-AMOUNT -- " op))))
           (else wrong-password-handler))))

(define (make-joint original-account original-password new-password)
  (define (wrong-password-handler useless-arg)
    (display "Incorrect another password"))

  (if (original-account original-password 'try-password)
    (lambda (input-password op)
      (if (eq? input-password new-password)
          (original-account original-password op)
          wrong-password-handler))
    (display "Incorrect original password")))

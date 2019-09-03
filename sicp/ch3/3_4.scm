(define (make-account balance password)
  (let ((max-password-try 7)
        (cur-password-fail-try 0))

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
      (if (eq? input-password password)
          (begin
            (set! cur-password-fail-try 0)
            #t)
          (begin
            (set! cur-password-fail-try (+ cur-password-fail-try 1))
            #f)))

    (define (call-the-cops)
      (error "You stand up"))

    (define (wrong-password-handler useless-arg)
      (if (<= cur-password-fail-try max-password-try)
          (display "Incorrect password")
          (call-the-cops)))


    (lambda (input-password op)
      (if (try-password input-password)
          (cond ((eq? op 'withdraw) withdraw)
                ((eq? op 'deposit) deposit)
                (else (error "Unknown request: MAKE-AMOUNT -- " op)))
          wrong-password-handler))))

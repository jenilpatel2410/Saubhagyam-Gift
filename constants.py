PROJECT_ENV = 1  # 0 for DEBUG, 1 for PRODUCTION


if PROJECT_ENV == 0:
    # config = Config(RepositoryEnv('.env/.env.dev'))
    PAYU_DATA = {
        "PAYU_REQUEST_URL": "https://test.payu.in/_payment",
        "PAYU_RESPONSE_BASE_URL": "https://gift.saubhagyam.com",
        "PAYU_KEY": "BOWzQR",
        # "PAYU_SALT": "pXUkvxo4YcBiOBv55dWW0CnAjwlwwO3v",
        "PAYU_SALT":"MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC/8vKpMG++eLASvq96seo/URiZ2dReI4PI3Pf0YqHlsNNWFwzg4DmwaKZ3dNdevH8YyuEmb75jmKM8Ez6sppVIa++lLAYN+d7m8s4DSh+MMYx5NrXNfXfcuJaWhq8ZGrQ/xAWseyBTl7lCxB7ZDdTQp4rIDBIuyHFnCvgL86FEmqwrPlsNx0+WP9sJ0ALh1lgIKgbo3p+0F7EogSbiI6OJQPagKxOwopWtKYqCuskpJ0rHcWXjRt6MqQGPaTsCEnOiwlniKxu4kidszeZdeFU9tNJ9Uf556w6DQbf4ErbZH0oX1OtEYdiVVP0ryPEMBum0v8q+mMHWFsDP4bCPhFOlAgMBAAECggEABUmz/sc27qPQvCqTFzfia18DHbV5wpW14kImyv9LRrYQ6NTMLQcZNt2wg9/0Cg8XF+3d/jr4Sd0BK/0Qn/KNjLY0gnPQIuMYxl5wBAb2LDH9P3ryean4M+qMHiTNt6JUzuDmkjmFPJL4A+tox3qqLXB5CxA8u/80EzyGdJsq0hETGxeHpxT9QitSGotvJifD4n8GwxhsyUEiBPQW25qQ3N3qzbDxB1zcytVM1BesYvDLEVijdWt3MyHGCMj0Idqf8kfvLMimr6kZzMx8PdK9jffglY7ff5vyeYwJvn5En4eU8+2V0DiOgYRSD9QLuLKRSnZtfleeUHWjq0UdOB4CLQKBgQDBtm6LHimGP2s+z4KvT48fjGns4X4NcmqXk9ZKf9MhgQp1iPRYYEn8zBcfTKigVbdOIsfQgLK+z6RBwI/z494QGrUoJnVJbWxhm2TNCUJtlNHM39RkbFqb/pEkfXYdVEl90X3CVK+Q8nmoiJJUuGh7SyeVpQt3aqVUEwd3cub7VwKBgQD9q1f0Tk5pp0l46KW5DyGr1ajz5pCf4fYdvlbZ+EWSKqsa6cgT/G+Dozif+0AEUFDu1oVT7mnQL7OesOKBkGoL5pjsDuOJzwehqMERcHYlkfcgIcAgV3hMjtN+p474lKPBWO8CjbZF5IgcQu+m2xG+EIZ1PSBM4dTRxTu1IeRHYwKBgQCaUi3KoqLOEmPrzAD+jNEmfwQ79IApUkdcrif/fcnDXTvp2steRIds32JkSvvjj6XSl567mmvL2zuuLiwATj4wcjZz3/98GbJIKDWrqn7DMdXZ808PGcstjyYt/c1FHErX8zbOxAyB2snU28hHuglyf7LvYma6IbnIOsit/lnJTQKBgQCcfU2/S2eYSjlLO8qwxaLyDNczz/M8jvt0Ee4mfcD9kREJg1uI6Nwqi1DtcORnRN0I2pJZ2uSwKB1ZMqopX9vsB5AjYHQCmhONKTwh9A0O1GNuESQjT5LJN/tFUT0kIR58ss6P9riRmZBWTvzlJJRnem5YeSMqCs9tsY1KCuR3HQKBgQCjoIkPzlza/zp+LSBZWadS2rnVkJp2+aeu+BzmoRZG5FQJSX6Nh4Nl4LO72Q1ISMePdGMUoeR5Er3RIkm3Qk2RVeh8agtzTfkZVjoeUFhwlxeYLyoMmF6AF5nU+1QYo/gYtyO3+olmBXoGHwzVXvIPj2tagAKKNs2fFPRjvLcMzQ==",
    }

if PROJECT_ENV == 1:
    #config = Config(RepositoryEnv('/home/ubuntu/SOSE/.env/.env.prod'))
    PAYU_DATA = {
        "PAYU_REQUEST_URL": "https://secure.payu.in/_payment",
        "PAYU_RESPONSE_BASE_URL": "https://gift.saubhagyam.com",
        "PAYU_KEY": "9PaBeB",
        "PAYU_SALT": "vuKsPuJeA49oqBt1KQB4Mh9E4CF8X4hQ",
    }

class Session:
    user_id = None
    name = None
    role = None
    applicant_id = None
    
    @classmethod
    def login(cls, user_row, applicat_row=None):
        cls.user_id, cls.name, cls.role, = user_row
        cls.applicant_id = applicat_row[0] if applicat_row else None
        
    @classmethod
    def logout(cls):
        cls.user_id = cls.name = cls.role = cls.applicant_id = None
from zerotk.appliance import Appliance


@Appliance.define
class Aws(Appliance):
    """
    Encapsulate access to AWS API so we can mock it for testing.
    """

    def list_profiles(self):
        import boto3
        session = boto3.Session()
        return session.available_profiles
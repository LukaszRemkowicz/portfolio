from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete, sender="astrophotography.AstroImage")
@receiver(pre_delete, sender="astrophotography.MainPageBackgroundImage")
@receiver(pre_delete, sender="programming.Project")
@receiver(pre_delete, sender="shop.ShopProduct")
@receiver(pre_delete, sender="shop.ShopSettings")
@receiver(pre_delete, sender="users.User")
def delete_image_variant_files_with_owner(sender, instance, **kwargs) -> None:
    """Delete variant rows transactionally and their files after commit."""
    if hasattr(instance, "variants"):
        instance.variants.using(kwargs["using"]).all().delete()

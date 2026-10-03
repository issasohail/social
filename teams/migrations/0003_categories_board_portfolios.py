from django.db import migrations, models
import django.db.models.deletion


def forward_fill(apps, schema_editor):
    TeamCategory = apps.get_model('teams', 'TeamCategory')
    TeamPosition = apps.get_model('teams', 'TeamPosition')
    Portfolio = apps.get_model('teams', 'Portfolio')
    Board = apps.get_model('boards', 'Board')

    # Convert the legacy free-text category into managed CRUD categories.
    categories = {}
    for pos in TeamPosition.objects.all():
        legacy = (getattr(pos, 'category_name', '') or '').strip()
        if not legacy:
            continue
        category, _ = TeamCategory.objects.get_or_create(
            name=legacy,
            defaults={'sort_order': {'Leadership': 10, 'Board': 20, 'Portfolio': 30}.get(legacy, 100)},
        )
        categories[legacy] = category
        pos.category_id = category.id
        pos.save(update_fields=['category'])

    # Existing portfolios were global. Attach them to the Social Welfare board
    # (prefer SWB; otherwise the first active board) before making board required.
    board = Board.objects.filter(code='SWB').first() or Board.objects.filter(is_active=True).order_by('sort_order', 'name').first() or Board.objects.order_by('id').first()
    if board:
        Portfolio.objects.filter(board__isnull=True).update(board=board)


def reverse_fill(apps, schema_editor):
    TeamPosition = apps.get_model('teams', 'TeamPosition')
    for pos in TeamPosition.objects.select_related('category').all():
        pos.category_name = pos.category.name if pos.category_id else ''
        pos.save(update_fields=['category_name'])


class Migration(migrations.Migration):
    dependencies = [
        ('teams', '0002_seed_demo_term_2026_2027'),
        ('boards', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name_plural': 'Team categories', 'ordering': ['sort_order', 'name']},
        ),
        migrations.RenameField(
            model_name='teamposition',
            old_name='category',
            new_name='category_name',
        ),
        migrations.AddField(
            model_name='teamposition',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='positions', to='teams.teamcategory'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='board',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='team_portfolios', to='boards.board'),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='name',
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='code',
            field=models.CharField(max_length=50),
        ),
        migrations.RunPython(forward_fill, reverse_fill),
        migrations.AlterField(
            model_name='portfolio',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='team_portfolios', to='boards.board'),
        ),
        migrations.AddConstraint(
            model_name='portfolio',
            constraint=models.UniqueConstraint(fields=('board', 'name'), name='unique_board_portfolio_name'),
        ),
        migrations.AddConstraint(
            model_name='portfolio',
            constraint=models.UniqueConstraint(fields=('board', 'code'), name='unique_board_portfolio_code'),
        ),
        migrations.RemoveField(
            model_name='teamposition',
            name='category_name',
        ),
    ]

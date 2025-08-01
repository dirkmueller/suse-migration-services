import io
from unittest.mock import (
    patch, Mock, MagicMock, call
)
from pytest import raises

from suse_migration_services.units.migrate import main, is_single_rpmtrans_requested
from suse_migration_services.defaults import Defaults
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


class TestMigration(object):
    @patch.object(Defaults, 'get_migration_config_file')
    def setup(self, mock_get_migration_config_file):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        self.migration_config = MigrationConfig()
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-verbose.yml'
        self.migration_config_verbose = MigrationConfig()
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-zypper-dup.yml'
        self.migration_config_dup = MigrationConfig()
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-solver-case.yml'
        self.migration_config_solver_case = MigrationConfig()

    @patch.object(Defaults, 'get_migration_config_file')
    def setup_method(self, cls, mock_get_migration_config_file):
        self.setup()

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_migration_plugin_raises(
        self, mock_MigrationConfig, mock_get_system_root_path,
        mock_update_env, mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        migration_config = Mock()
        migration_config.get_migration_product.return_value = 'product'
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        mock_Command_run.side_effect = Exception
        mock_get_system_root_path.return_value = '../data'
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            with raises(DistMigrationZypperException):
                main()

            assert mock_open.call_args_list == [
                call('../data/etc/issue', 'w'),
                call('/var/log/distro_migration.exitcode', 'w')
            ]
            assert file_handle.write.call_args_list == [
                call(
                    'Migration has failed, for further details see {0}'.format(
                        '/var/log/distro_migration.log'
                    )
                ),
                call('1\n')
            ]

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_dup_raises(
        self, mock_MigrationConfig, mock_get_system_root_path,
        mock_update_env, mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            False
        mock_MigrationConfig.return_value = migration_config
        zypper_call = Mock()
        zypper_call.returncode = 0
        mock_Command_run.return_value = zypper_call
        mock_get_system_root_path.return_value = '../data'
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True):
            # zypper exit code is 0, all ok
            main()

        with patch('builtins.open', create=True):
            # zypper exit code is 1, error
            zypper_call.returncode = 1
            with raises(DistMigrationZypperException):
                main()

        with patch('builtins.open', create=True):
            # zypper exit code is 104, error
            zypper_call.returncode = 104
            with raises(DistMigrationZypperException):
                main()

        with patch('builtins.open', create=True):
            # zypper exit code is 105, error
            zypper_call.returncode = 105
            with raises(DistMigrationZypperException):
                main()

        with patch('builtins.open', create=True):
            # zypper exit code is 106, error
            zypper_call.returncode = 106
            with raises(DistMigrationZypperException):
                main()

        with patch('builtins.open', create=True):
            # zypper exit code is 107, all ok
            zypper_call.returncode = 107
            main()

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch.object(MigrationConfig, 'get_migration_product')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_migration_plugin(
        self, mock_MigrationConfig, mock_get_system_root_path,
        mock_update_env, mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        mock_MigrationConfig.return_value = self.migration_config
        mock_get_system_root_path.return_value = 'SLES/15/x86_64'
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            main()

        mock_open.assert_called_once_with(
            '/var/log/distro_migration.exitcode', 'w'
        )
        file_handle.write.assert_called_once_with('0\n')
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper migration '
                '--no-verbose '
                ' '
                '--non-interactive '
                '--gpg-auto-import-keys '
                '--no-selfupdate '
                '--auto-agree-with-licenses '
                '--allow-vendor-change '
                '--strict-errors-dist-migration '
                '--replacefiles '
                '--product SLES/15/x86_64 '
                '--root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ]
        )

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch.object(MigrationConfig, 'get_migration_product')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_migration_plugin_verbose(
        self, mock_MigrationConfig, mock_get_system_root_path,
        mock_update_env, mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        mock_MigrationConfig.return_value = self.migration_config_verbose
        mock_get_system_root_path.return_value = 'SLES/15/x86_64'
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True):
            main()
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper migration '
                '--verbose '
                ' '
                '--non-interactive '
                '--gpg-auto-import-keys '
                '--no-selfupdate '
                '--auto-agree-with-licenses '
                '--allow-vendor-change '
                '--strict-errors-dist-migration '
                '--replacefiles '
                '--product SLES/15/x86_64 '
                '--root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ]
        )

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch.object(MigrationConfig, 'get_migration_product')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_migration_plugin_solver_case(
        self, mock_MigrationConfig, mock_get_system_root_path,
        mock_update_env, mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        mock_MigrationConfig.return_value = self.migration_config_solver_case
        mock_get_system_root_path.return_value = 'SLES/15/x86_64'
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True):
            main()
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper migration '
                '--no-verbose '
                '--debug-solver '
                '--non-interactive '
                '--gpg-auto-import-keys '
                '--no-selfupdate '
                '--auto-agree-with-licenses '
                '--allow-vendor-change '
                '--strict-errors-dist-migration '
                '--replacefiles '
                '--product SLES/15/x86_64 '
                '--root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ]
        )

    @patch('suse_migration_services.units.migrate.is_single_rpmtrans_requested')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.log_env')
    @patch('suse_migration_services.units.migrate.update_env')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    def test_main_zypper_dup(
        self, mock_MigrationConfig, mock_update_env,
        mock_log_env, mock_Command_run, mock_logger_setup,
        mock_is_single_rpmtrans_requested
    ):
        mock_MigrationConfig.return_value = self.migration_config_dup
        zypper_call = Mock()
        zypper_call.returncode = 0
        mock_Command_run.return_value = zypper_call
        mock_is_single_rpmtrans_requested.return_value = '0'
        with patch('builtins.open', create=True):
            main()
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper --no-cd --non-interactive '
                '--gpg-auto-import-keys '
                '--root /system-root '
                'dup '
                '--auto-agree-with-licenses '
                '--allow-vendor-change '
                '--download in-advance '
                '--replacefiles '
                '--allow-downgrade '

                '&>> /system-root/var/log/distro_migration.log'
            ], raise_on_error=False
        )

    @patch('builtins.open', new_callable=MagicMock)
    def test_is_single_rpmtrans_requested(self, mock_open):
        # Test case 1: migration.single_rpmtrans is not present
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default root=/dev/sda2'
        assert is_single_rpmtrans_requested() == '0'

        # Test case 2: migration.single_rpmtrans=true
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default migration.single_rpmtrans=true'
        assert is_single_rpmtrans_requested() == '1'

        # Test case 3: migration.single_rpmtrans=1
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default migration.single_rpmtrans=1'
        assert is_single_rpmtrans_requested() == '1'

        # Test case 4: migration.single_rpmtrans=false
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default migration.single_rpmtrans=false'
        assert is_single_rpmtrans_requested() == '0'

        # Test case 5: migration.single_rpmtrans=0
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default migration.single_rpmtrans=0'
        assert is_single_rpmtrans_requested() == '0'

        # Test case 6: migration.single_rpmtrans with unexpected value
        mock_open.return_value.__enter__.return_value.read.return_value = \
            'BOOT_IMAGE=/boot/vmlinuz-5.3.18-150300.59.87-default migration.single_rpmtrans=unexpected'
        assert is_single_rpmtrans_requested() == '0'

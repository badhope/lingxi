"""
认证系统测试
验证用户认证、权限管理和会话管理功能
"""
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("DataAgent 认证系统测试")
print("=" * 70)

all_tests_passed = True

try:
    from core import (
        auth_manager,
        UserRole,
        Permission,
        hash_password,
        verify_password,
    )
    
    print("\n✅ 认证模块导入成功")
    
    # 测试 1: 检查默认管理员是否创建
    print("\n📋 测试 1: 检查默认管理员")
    users = auth_manager.list_users(include_inactive=True)
    print(f"  用户总数: {len(users)}")
    
    admin_user = auth_manager.get_user_by_username("admin")
    if admin_user:
        print(f"  ✓ 找到默认管理员: {admin_user.username}")
        print(f"    邮箱: {admin_user.email}")
        print(f"    角色: {admin_user.role.value}")
        print(f"    状态: {'活跃' if admin_user.is_active else '禁用'}")
    else:
        print("  ✗ 未找到默认管理员")
        all_tests_passed = False
    
    # 测试 2: 密码哈希和验证
    print("\n📋 测试 2: 密码哈希和验证")
    test_password = "testpassword123"
    hashed, salt = hash_password(test_password)
    print(f"  ✓ 密码哈希生成成功")
    print(f"    Salt: {salt[:10]}...")
    print(f"    Hash: {hashed[:20]}...")
    
    # 验证正确密码
    if verify_password(test_password, hashed):
        print("  ✓ 正确密码验证成功")
    else:
        print("  ✗ 正确密码验证失败")
        all_tests_passed = False
    
    # 验证错误密码
    if not verify_password("wrongpassword", hashed):
        print("  ✓ 错误密码验证失败（预期行为）")
    else:
        print("  ✗ 错误密码验证通过（不应发生）")
        all_tests_passed = False
    
    # 测试 3: 用户认证
    print("\n📋 测试 3: 用户认证")
    
    # 测试默认管理员登录
    session = auth_manager.authenticate("admin", "admin123")
    if session:
        print(f"  ✓ 管理员认证成功")
        print(f"    会话 Token: {session.token[:15]}...")
        print(f"    过期时间: {session.expires_at}")
        
        # 验证会话
        verified_user = auth_manager.verify_session(session.token)
        if verified_user and verified_user.username == "admin":
            print("  ✓ 会话验证成功")
        else:
            print("  ✗ 会话验证失败")
            all_tests_passed = False
        
        # 撤销会话
        auth_manager.revoke_session(session.token)
        revoked_check = auth_manager.verify_session(session.token)
        if not revoked_check:
            print("  ✓ 会话撤销成功")
        else:
            print("  ✗ 会话撤销失败")
            all_tests_passed = False
    else:
        print("  ✗ 管理员认证失败（默认密码应该是 admin123）")
        all_tests_passed = False
    
    # 测试 4: 创建新用户
    print("\n📋 测试 4: 创建新用户")
    try:
        new_user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=UserRole.USER,
            display_name="测试用户"
        )
        print(f"  ✓ 新用户创建成功: {new_user.username}")
        print(f"    用户 ID: {new_user.id}")
        print(f"    角色: {new_user.role.value}")
        
        # 测试新用户登录
        new_session = auth_manager.authenticate("testuser", "testpass123")
        if new_session:
            print("  ✓ 新用户认证成功")
        else:
            print("  ✗ 新用户认证失败")
            all_tests_passed = False
        
    except ValueError as e:
        print(f"  ✗ 用户创建失败: {e}")
        all_tests_passed = False
    
    # 测试 5: 权限检查
    print("\n📋 测试 5: 权限检查")
    if admin_user:
        # 管理员应该有所有权限
        admin_has_all = admin_user.has_permission(Permission.MANAGE_USERS)
        if admin_has_all:
            print("  ✓ 管理员有用户管理权限")
        else:
            print("  ✗ 管理员权限检查失败")
            all_tests_passed = False
        
        admin_has_agent = admin_user.has_permission(Permission.USE_AGENT)
        if admin_has_agent:
            print("  ✓ 管理员有 Agent 使用权限")
        else:
            print("  ✗ 管理员权限检查失败")
            all_tests_passed = False
    
    # 检查普通用户权限
    test_user = auth_manager.get_user_by_username("testuser")
    if test_user:
        user_has_agent = test_user.has_permission(Permission.USE_AGENT)
        if user_has_agent:
            print("  ✓ 普通用户有 Agent 使用权限")
        else:
            print("  ✗ 普通用户权限检查失败")
            all_tests_passed = False
        
        # 普通用户不应有用户管理权限
        user_has_user_manage = test_user.has_permission(Permission.MANAGE_USERS)
        if not user_has_user_manage:
            print("  ✓ 普通用户没有用户管理权限（预期行为）")
        else:
            print("  ✗ 普通用户权限检查异常")
            all_tests_passed = False
    
    # 测试 6: 用户信息更新
    print("\n📋 测试 6: 用户信息更新")
    test_user = auth_manager.get_user_by_username("testuser")
    if test_user:
        updated_user = auth_manager.update_user(
            test_user.id,
            display_name="更新后的测试用户",
            email="updated@example.com"
        )
        if updated_user:
            print(f"  ✓ 用户信息更新成功")
            print(f"    新的显示名: {updated_user.display_name}")
            print(f"    新的邮箱: {updated_user.email}")
        else:
            print("  ✗ 用户信息更新失败")
            all_tests_passed = False
    
    # 测试 7: 列出所有用户
    print("\n📋 测试 7: 列出用户")
    all_users = auth_manager.list_users()
    print(f"  ✓ 成功获取用户列表，总用户数: {len(all_users)}")
    for user in all_users:
        print(f"    - {user.username} ({user.role.value})")
    
    # 测试 8: 用户删除（清理测试用户）
    print("\n📋 测试 8: 用户删除")
    test_user = auth_manager.get_user_by_username("testuser")
    if test_user:
        delete_success = auth_manager.delete_user(test_user.id)
        if delete_success:
            print("  ✓ 测试用户删除成功")
        else:
            print("  ✗ 用户删除失败")
            all_tests_passed = False
    
    # 验证用户确实被删除了
    deleted_check = auth_manager.get_user_by_username("testuser")
    if not deleted_check:
        print("  ✓ 确认用户已删除")
    else:
        print("  ✗ 用户删除验证失败")
        all_tests_passed = False
    
    # 总结
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("🎉 认证系统测试通过！")
        print("\n📋 系统状态:")
        print("  - 认证模块正常工作")
        print("  - 默认管理员已创建 (用户名: admin, 密码: admin123)")
        print("  - 权限系统正常")
        print("  - 会话管理正常")
        print("\n⚠️  重要提示: 请立即修改默认管理员密码！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ 测试执行失败: {e}")
    import traceback
    traceback.print_exc()
    all_tests_passed = False
    sys.exit(1)

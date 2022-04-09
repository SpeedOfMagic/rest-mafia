from rest.profile_dao import Profile, ProfileDao
import os


def test_dao_init():
    ProfileDao()
    assert os.path.exists(ProfileDao.DB_PATH)
    assert len(open(ProfileDao.DB_PATH).read()) > 0
    os.remove(ProfileDao.DB_PATH)


BASE_PROFILE = Profile(
    login='a',
    password='b',
    name='c',
    image=b'd',
    gender='e',
    mail='f',
    total_time=7,
    session_count=8,
    win_count=9,
    lose_count=10,
)


def test_dao_get_profile():
    dao = ProfileDao()
    dao.insert_profile(BASE_PROFILE)

    dao_profile = dao.lookup_profile(BASE_PROFILE.login)
    assert vars(dao_profile) == vars(BASE_PROFILE)

    del dao
    os.remove(ProfileDao.DB_PATH)


def test_dao_modify_profile():
    dao = ProfileDao()
    dao.insert_profile(BASE_PROFILE)

    dao.modify_profile(login=BASE_PROFILE.login, mail='mymail@box.com', gender='Female')
    new_profile = dao.lookup_profile(BASE_PROFILE.login)
    assert new_profile.mail == 'mymail@box.com'
    assert new_profile.gender == 'Female'
    new_profile.mail, new_profile.gender = BASE_PROFILE.mail, BASE_PROFILE.gender
    assert vars(new_profile) == vars(BASE_PROFILE)

    del dao
    os.remove(ProfileDao.DB_PATH)


def test_dao_finish_game():
    dao = ProfileDao()
    dao.insert_profile(BASE_PROFILE)

    dao.finish_game(BASE_PROFILE.login, 100, True)
    profile = dao.lookup_profile(BASE_PROFILE.login)
    assert profile.total_time == BASE_PROFILE.total_time + 100
    assert profile.session_count == BASE_PROFILE.session_count + 1
    assert profile.win_count == BASE_PROFILE.win_count + 1
    assert profile.lose_count == BASE_PROFILE.lose_count

    dao.finish_game(BASE_PROFILE.login, 1000, False)
    profile = dao.lookup_profile(BASE_PROFILE.login)
    assert profile.total_time == BASE_PROFILE.total_time + 1100
    assert profile.session_count == BASE_PROFILE.session_count + 2
    assert profile.win_count == BASE_PROFILE.win_count + 1
    assert profile.lose_count == BASE_PROFILE.lose_count + 1

    del dao
    os.remove(ProfileDao.DB_PATH)

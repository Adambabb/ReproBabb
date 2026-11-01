import pytest
from PySide6.QtCore import QObject, Signal

from song_queue import SongQueue


class FakePlayer(QObject):
    state_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.stopped = False

    def stop(self):
        self.stopped = True


def make_songs(n):
    return [{"id": f"id{i}", "title": f"Song {i}"} for i in range(n)]


@pytest.fixture
def queue():
    q = SongQueue(FakePlayer())
    q.songs_list = make_songs(4)
    q.model.set_songs(q.songs_list)
    q.fetched = []
    q.start_fetch = lambda song: q.fetched.append(song["id"])
    return q


def test_get_song_index_returns_current_song(queue):
    queue.current_index = 2
    assert queue.get_song_index()["id"] == "id2"


def test_get_song_index_returns_none_if_no_current_song(queue):
    queue.current_index = len(queue.songs_list)
    assert queue.get_song_index() is None


def test_increment_current_index(queue):
    queue.current_index = 1
    queue.increment_index()
    assert queue.current_index == 2


def test_increment_current_index_shuffled(queue):
    queue.shuffle_queue()
    queue.increment_index()
    assert queue.is_shuffle is True
    assert queue.shuffle_current_index == 1


def test_increment_index_past_last_song(queue):
    queue.current_index = len(queue.songs_list) - 1
    queue.increment_index()
    assert queue.get_song_index() is None


def test_increment_index_past_last_song_shuffled(queue):
    queue.shuffle_queue()
    queue.shuffle_current_index = len(queue.shuffle_song_list) - 1
    queue.increment_index()

    assert queue.get_song_index() is None


def test_increment_index_past_last_song_empty_queue(queue):
    queue.songs_list = []
    queue.current_index = 0
    queue.increment_index()
    assert queue.get_song_index() is None


def test_increment_index_past_last_song_empty_queue_shuffled(queue):
    queue.is_shuffle = True
    queue.songs_list = []
    queue.current_index = 0
    queue.shuffle_current_index = 0
    queue.increment_index()

    assert queue.get_song_index() is None


def test_next_or_previous_and_counts_clicks_next(queue):
    queue.next_or_previous("next")
    queue.next_or_previous("next")
    queue.next_or_previous("next")

    assert queue.click_count == 3


def test_next_or_previous_and_counts_clicks_previous(queue):
    queue.next_or_previous("previous")
    queue.next_or_previous("previous")
    queue.next_or_previous("previous")

    assert queue.click_count == -3


def test_next_or_previous_invalid_direction_raises_error(queue):
    with pytest.raises(ValueError):
        queue.next_or_previous("adios")


def test_add_song_to_queue(queue):
    new_song = {"id": "id4", "title": "Song 4"}
    queue.add_to_queue(new_song)
    insert_index = queue.current_index + 1
    assert queue.songs_list[insert_index] == new_song


def test_add_song_to_queue_shuffled(queue):
    queue.shuffle_queue()
    new_song = {"id": "id4", "title": "Song 4"}

    expected_real_index = len(queue.songs_list)
    target_shuffle_index = queue.shuffle_current_index + 1

    queue.add_to_queue(new_song)

    assert queue.songs_list[-1] == new_song

    assert queue.shuffle_song_list[target_shuffle_index] == expected_real_index


def test_add_song_to_queue_empty_queue(queue):
    queue.songs_list = []
    queue.current_index = 0
    new_song = {"id": "id0", "title": "Song 0"}
    queue.add_to_queue(new_song)
    assert queue.songs_list[0] == new_song


def test_add_song_to_queue_empty_queue_shuffled(queue):
    queue.songs_list = []
    queue.current_index = 0
    queue.is_shuffle = True
    queue.shuffle_current_index = 0
    new_song = {"id": "id0", "title": "Song 0"}
    queue.add_to_queue(new_song)
    assert queue.songs_list[0] == new_song
    assert queue.shuffle_song_list[0] == 0


def test_add_multiple_songs_to_queue(queue):
    new_songs = [
        {"id": "id4", "title": "Song 4"},
        {"id": "id5", "title": "Song 5"},
    ]
    queue.add_multiple_to_queue(new_songs)
    insert_index = queue.current_index + 1
    assert queue.songs_list[insert_index : insert_index + len(new_songs)] == new_songs


def test_add_multiple_songs_to_queue_shuffled(queue):
    queue.shuffle_queue()
    new_songs = [
        {"id": "id4", "title": "Song 4"},
        {"id": "id5", "title": "Song 5"},
    ]

    expected_real_index = len(queue.songs_list)
    target_shuffle_index = queue.shuffle_current_index + 1

    queue.add_multiple_to_queue(new_songs)

    assert queue.songs_list[-len(new_songs) :] == new_songs

    assert queue.shuffle_song_list[
        target_shuffle_index : target_shuffle_index + len(new_songs)
    ] == list(range(expected_real_index, expected_real_index + len(new_songs)))


def test_add_multiple_songs_to_queue_empty_queue(queue):
    queue.songs_list = []
    queue.current_index = 0
    new_songs = [
        {"id": "id0", "title": "Song 0"},
        {"id": "id1", "title": "Song 1"},
    ]
    queue.add_multiple_to_queue(new_songs)
    assert queue.songs_list == new_songs


def test_reorder_queue_updates_song_list(queue):
    expected_order = list(reversed(queue.songs_list))

    queue.reorder_queue(expected_order)

    assert queue.songs_list == expected_order


def test_reorder_queue_updates_current_index(queue):
    queue.current_index = 1
    playing_song = queue.songs_list[1]

    new_order = list(reversed(queue.songs_list))
    queue.reorder_queue(new_order)

    assert queue.songs_list[queue.current_index] == playing_song
    assert queue.current_index == 2


def test_reorder_queue_updates_shuffle_song_list(queue):
    queue.shuffle_queue()
    queue.shuffle_current_index = 1
    playing_song = queue.songs_list[queue.shuffle_song_list[1]]

    new_order = list(reversed(queue.songs_list))
    queue.reorder_queue(new_order)

    assert (
        queue.songs_list[queue.shuffle_song_list[queue.shuffle_current_index]]
        == playing_song
    )


def test_reorder_queue_without_playing_song(queue):
    queue.current_index = len(queue.songs_list)
    playing_song = queue.songs_list[1]

    new_order = list(reversed(queue.songs_list))
    new_order.remove(playing_song)
    queue.reorder_queue(new_order)

    assert queue.get_song_index() is None


def test_remove_song_after_current_index(queue):
    queue.current_index = 1
    playing_song = queue.songs_list[1]

    queue.remove_song_at_index(2)

    assert queue.current_index == 1
    assert queue.get_song_index() == playing_song


def test_remove_song_before_current_index(queue):
    queue.current_index = 2
    playing_song = queue.songs_list[2]

    queue.remove_song_at_index(0)

    assert queue.current_index == 1
    assert queue.get_song_index() == playing_song


def test_remove_currently_playing_song(queue):
    queue.current_index = 1
    next_song = queue.songs_list[2]
    queue.fetched.clear()
    queue.remove_song_at_index(1)

    assert queue.current_index == 1
    assert queue.get_song_index() == next_song
    assert queue.fetched == [next_song["id"]]


def test_remove_song_before_current_index_shuffled(queue):
    queue.shuffle_queue()
    queue.shuffle_current_index = 2
    playing_song = queue.songs_list[queue.shuffle_song_list[2]]

    queue.remove_song_at_index(0)

    assert queue.shuffle_current_index == 1
    assert (
        queue.songs_list[queue.shuffle_song_list[queue.shuffle_current_index]]
        == playing_song
    )


def test_remove_song_after_current_index_shuffled(queue):
    queue.shuffle_queue()
    queue.shuffle_current_index = 1
    playing_song = queue.songs_list[queue.shuffle_song_list[1]]

    queue.remove_song_at_index(2)

    assert queue.shuffle_current_index == 1
    assert (
        queue.songs_list[queue.shuffle_song_list[queue.shuffle_current_index]]
        == playing_song
    )


def test_remove_song_shuffled_updates_shuffle_list(queue):
    queue.shuffle_queue()
    initial_len = len(queue.shuffle_song_list)

    queue.remove_song_at_index(0)

    assert len(queue.shuffle_song_list) == initial_len - 1


def test_remove_currently_playing_song_shuffled(queue):
    queue.shuffle_queue()
    queue.shuffle_current_index = 1
    next_song = queue.songs_list[queue.shuffle_song_list[2]]

    queue.fetched.clear()
    queue.remove_song_at_index(1)

    assert queue.shuffle_current_index == 1
    assert (
        queue.songs_list[queue.shuffle_song_list[queue.shuffle_current_index]]
        == next_song
    )
    assert queue.fetched == [next_song["id"]]


def test_remove_last_playing_song(queue):
    queue.current_index = 0
    queue.songs_list = make_songs(1)

    queue.fetched.clear()
    queue.remove_song_at_index(queue.current_index)

    assert queue.current_index == len(queue.songs_list)
    assert queue.player.stopped is True
    assert queue.get_song_index() is None
    assert queue.fetched == []


def test_remove_last_playing_song_shuffled(queue):
    queue.current_index = 0
    queue.songs_list = make_songs(1)
    queue.shuffle_queue()

    queue.fetched.clear()
    queue.remove_song_at_index(queue.current_index)

    assert queue.current_index == len(queue.songs_list)
    assert queue.shuffle_current_index == len(queue.shuffle_song_list)
    assert queue.player.stopped is True
    assert queue.get_song_index() is None
    assert queue.fetched == []


def test_remove_song_finished_queue(queue):
    queue.current_index = len(queue.songs_list)

    queue.fetched.clear()

    queue.remove_song_at_index(queue.current_index)

    assert queue.get_song_index() is None
    assert queue.fetched == []


def test_remove_song_finished_queue_shuffled(queue):
    queue.current_index = len(queue.songs_list)
    queue.shuffle_queue()
    queue.shuffle_current_index = len(queue.shuffle_song_list)

    queue.fetched.clear()

    queue.remove_song_at_index(queue.shuffle_current_index)

    assert queue.get_song_index() is None
    assert queue.fetched == []

from DownloadQueue import DownloadQueue


def test_register_download_starts_pending():
    queue = DownloadQueue()

    download_id = queue.register_download("Song A")

    data = queue.get_data()
    assert data[download_id]["title"] == "Song A"
    assert data[download_id]["status"] == "pending"
    assert data[download_id]["progress"] == 0


def test_each_download_gets_a_different_id():
    queue = DownloadQueue()

    first = queue.register_download("Song A")
    second = queue.register_download("Song B")

    assert first != second


def test_update_progress():
    queue = DownloadQueue()

    download_id = queue.register_download("Song A")
    queue.update_progress(download_id, 50)

    assert queue.get_data()[download_id]["progress"] == 50


def test_update_progress_with_unknown_id_does_nothing():
    queue = DownloadQueue()

    queue.update_progress(999, 50)

    assert queue.get_data() == {}


def test_start_download_marks_it_downloading():
    queue = DownloadQueue()

    queue.register_download("Song A")

    download_id = queue.register_download("Song B")
    result = queue.start_download(download_id)

    assert queue.get_data()[download_id]["status"] == "downloading"
    assert result is True


def test_start_download_refuses_cancelled_download():
    queue = DownloadQueue()

    download_id = queue.register_download("Song A")
    queue.cancel_download(download_id)

    result = queue.start_download(download_id)

    assert queue.get_data()[download_id]["status"] == "cancelled"
    assert result is False


def test_start_download_with_unknown_id_returns_false():
    queue = DownloadQueue()

    result = queue.start_download(999)

    assert result is False


def test_cancel_download_marks_it_cancelled():
    queue = DownloadQueue()

    queue.register_download("Song A")
    download_id = queue.register_download("Song B")
    queue.cancel_download(download_id)

    assert queue.get_data()[download_id]["status"] == "cancelled"
    assert queue.is_cancelled(download_id) is True


def test_is_cancelled_is_false_by_default():
    queue = DownloadQueue()

    download_id = queue.register_download("Song A")

    assert queue.is_cancelled(download_id) is False


def test_update_status_with_unknown_id_does_nothing():
    queue = DownloadQueue()

    queue.update_status(999, "downloading")

    assert queue.get_data() == {}


def test_update_status_changes_status():
    queue = DownloadQueue()

    download_id = queue.register_download("Song A")
    queue.update_status(download_id, "downloading")

    assert queue.get_data()[download_id]["status"] == "downloading"

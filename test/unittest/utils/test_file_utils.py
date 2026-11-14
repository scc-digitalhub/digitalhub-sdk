from hashlib import sha256

from digitalhub.utils import file_utils


def test_calculate_blob_hash_reads_file_in_chunks(tmp_path, monkeypatch) -> None:
    chunk_size = 1024 * 1024
    data = b"x" * (2 * chunk_size + 17)
    path = tmp_path / "large.bin"
    path.write_bytes(data)
    real_open = open
    read_sizes = []

    class TrackingFile:
        def __init__(self, file) -> None:
            self.file = file

        def __enter__(self):
            return self

        def __exit__(self, *exc_info) -> None:
            self.file.close()

        def read(self, size: int) -> bytes:
            read_sizes.append(size)
            return self.file.read(size)

    monkeypatch.setattr(
        file_utils,
        "open",
        lambda file_path, mode: TrackingFile(real_open(file_path, mode)),
        raising=False,
    )

    assert file_utils.calculate_blob_hash(str(path)) == f"sha256:{sha256(data).hexdigest()}"
    assert len(read_sizes) == 4
    assert all(size == chunk_size for size in read_sizes)

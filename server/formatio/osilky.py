
import zipfile
from zipfile import ZipFile
import io
import json
from tempfile import NamedTemporaryFile, TemporaryDirectory
import struct
import os
import os.path

from silky import MeasureType


def write(dataset, path):

    with ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zip:
        content = io.StringIO()
        content.write('Manifest-Version: 1.0\n')
        content.write('Created-By: JASP 0.7.5 Beta 2\n')
        content.write('Data-Archive-Version: 1.0.2\n')
        content.write('JASP-Archive-Version: 2.0\n')
        zip.writestr('META-INF/MANIFEST.MF', bytes(content.getvalue(), 'utf-8'), zipfile.ZIP_DEFLATED)

        content = None

        fields = [ ]
        for column in dataset:
            field = { }
            field['name'] = column.name
            field['measureType'] = MeasureType.stringify(column.type)
            if column.type == MeasureType.CONTINUOUS:
                field['type'] = 'number'
            else:
                field['type'] = 'integer'
            fields.append(field)

        metadata = { }

        metadataset = { }
        metadataset['rowCount'] = dataset.row_count
        metadataset['columnCount'] = dataset.column_count
        metadataset['fields'] = fields

        metadata['dataSet'] = metadataset

        zip.writestr('metadata.json', json.dumps(metadata), zipfile.ZIP_DEFLATED)

        metadata = None

        xdata = { }
        for column in dataset:
            if column.has_labels:
                xdata[column.name] = column.labels
        zip.writestr('xdata.json', json.dumps(xdata), zipfile.ZIP_DEFLATED)
        xdata = None

        row_count = dataset.row_count
        required_bytes = 0
        for column in dataset:
            if column.type == MeasureType.CONTINUOUS:
                required_bytes += (8 * row_count)
            else:
                required_bytes += (4 * row_count)

        temp_file = NamedTemporaryFile(delete=False)
        temp_file.truncate(required_bytes)

        for column in dataset:
            if column.type == MeasureType.CONTINUOUS:
                for i in range(0, row_count):
                    value = column.raw(i)
                    byts = struct.pack('<d', value)
                    temp_file.write(byts)
            else:
                for i in range(0, row_count):
                    value = column.raw(i)
                    byts = struct.pack('<i', value)
                    temp_file.write(byts)

        temp_file.close()

        zip.write(temp_file.name, 'data.bin')
        os.remove(temp_file.name)


def read(dataset, path):

    with ZipFile(path, 'r') as zip:
        # manifest = zip.read('META-INF/MANIFEST.MF')

        meta_content = zip.read('metadata.json').decode('utf-8')
        metadata = json.loads(meta_content)
        meta_dataset = metadata['dataSet']

        for meta_column in meta_dataset['fields']:
            dataset.append_column(meta_column['name'])
            column = dataset[dataset.column_count - 1]
            measure_type = MeasureType.parse(meta_column['measureType'])
            column.type = measure_type

        row_count = meta_dataset['rowCount']

        for i in range(row_count):
            dataset.append_row()
            for column in dataset:
                column[i] = 0

        with TemporaryDirectory() as dir:
            zip.extract('data.bin', dir)
            data_path = os.path.join(dir, 'data.bin')
            data_file = open(data_path, 'rb')

            for column in dataset:
                if column.type == MeasureType.CONTINUOUS:
                    for i in range(row_count):
                        byts = data_file.read(8)
                        value = struct.unpack('<d', byts)
                        column[i] = value[0]
                else:
                    for i in range(row_count):
                        byts = data_file.read(4)
                        value = struct.unpack('<i', byts)
                        column[i] = value[0]
            data_file.close()

        xdata_content = zip.read('xdata.json').decode('utf-8')
        xdata = json.loads(xdata_content)

        for column in dataset:
            if column.name in xdata:
                meta_labels = xdata[column.name]
                for meta_label in meta_labels:
                    column.add_label(meta_label[0], meta_label[1])

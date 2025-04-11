from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json

notes = Blueprint('notes', __name__, template_folder='templates/notes_templates')


@notes.route('/uzrasai', methods=['GET', 'POST'])
@login_required
def uzrasai_page():
    if request.method == 'POST':
        note_id = request.form.get('note_id')  # Retrieve the note ID if editing
        note_content = request.form.get('note')
        tags = request.form.get('tags').strip()  # Get tags and strip whitespace

        if len(note_content) < 1:
            flash('Užrašas per trumpas', category='error')
        else:
            if note_id:  # Update existing note
                note = Note.query.get(note_id)
                if note and note.user_id == current_user.id:
                    note.data = note_content
                    # Only update tags if a new value was provided
                    if tags:
                        note.tags = tags
                    flash('Užrašas atnaujintas!', category='success')
            else:  # Add new note
                new_note = Note(data=note_content, tags=tags, user_id=current_user.id)
                db.session.add(new_note)
                flash('Užrašas pridėtas!', category='success')
            db.session.commit()

    # Retrieve notes with pinned notes at the top
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.pinned.desc(), Note.date.desc()).all()
    return render_template("uzrasai_page.html", user=current_user, notes=notes)


@notes.route('/get-note-content/<int:note_id>', methods=['GET'])
@login_required
def get_note_content(note_id):
    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        return jsonify({"content": note.data})
    return jsonify({"error": "Užrašas nerastas arba priega neleistina"}), 404


@notes.route('/toggle-pin', methods=['POST'])
@login_required
def toggle_pin():
    note_id = request.json.get('noteId')
    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        note.pinned = not note.pinned  # Toggle the pinned status
        db.session.commit()
    return jsonify(success=True, pinned=note.pinned)  # Return the new pin status


@notes.route('/get-notes')
@login_required
def get_notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.pinned.desc(), Note.date.desc()).all()
    notes_data = [
        {
            "id": note.id,
            "data": note.data,
            "tags": note.tags,
            "date": note.date.isoformat(),
            "pinned": note.pinned
        }
        for note in notes
    ]
    return jsonify(notes_data)


@notes.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})






